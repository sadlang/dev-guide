#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
كاشف انجراف الدليل (drift checker) عن مصادره في مستودع اللغة + حُرّاسه.

يربط sync/sources.yaml كلَّ فصلٍ بمصادره الحقيقيّة في مستودع اللغة. لكل مصدر
بصمةٌ نقارنها بـsync/sources.lock.json:
  - ملفّ/مجلد كامل: بصمة git (blob/tree sha) عبر `gh api .../contents`.
  - نطاق أسطر (تقليل الضجيج): نجلب المحتوى الخام، نقتطع النطاق، ونبصمه sha256.
    هكذا لا يُطلِق تعديلٌ خارج النطاق إنذارًا كاذبًا، ويُرصد «تعفّن» المنطقة الموثَّقة.

الأطوار:
  (افتراضيّ)        فحص وتقرير؛ يفشل (1) عند الانجراف.
  --json            تقرير JSON للأتمتة.
  --update          يثبّت البصمات الحاليّة (بعد مراجعة الدليل).
  --ref REF         يتجاوز ref البيان (مثلًا وسم إصدار: v1.2.0) — لربط المزامنة بالإصدارات.
  --set-version V   مع --update: يكتب covers_version=V في القفل (ارفعه عند مراجعة إصدار).
  --validate        حارس بلا شبكة: يتحقّق من سلامة البيان (مسارات الفصول، تكرار المفاتيح،
                    صيغة الأسطر، وأن كل فصل تقنيّ في SUMMARY مسجَّل).
  --guard-lock ...  حارس CI: يمنع «الكتم الصامت» — يرفض تقدّم القفل دون تعديل الفصل المعنيّ.

الاستعمال النموذجيّ:
    python scripts/check_sync.py                       # فحص (يفشل عند الانجراف)
    python scripts/check_sync.py --update              # تثبيت بعد المراجعة
    python scripts/check_sync.py --ref v1.2.0 --update --set-version 1.2.0
    python scripts/check_sync.py --validate            # في CI
    python scripts/check_sync.py --guard-lock --base base.json --changed-files files.txt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ينقص الاعتماد: pip install pyyaml")

# اطبع UTF-8 دائمًا (وحدة تحكّم ويندوز قد تكون cp1252/cp1255)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sync" / "sources.yaml"
LOCKFILE = ROOT / "sync" / "sources.lock.json"
SUMMARY = ROOT / "src" / "SUMMARY.md"


# ── تطبيع المصادر ──────────────────────────────────────────────────────────────
def normalize_source(s) -> dict:
    """يحوّل مصدرًا (نصّ أو كائن {path, lines}) إلى صيغة موحّدة بمفتاح فريد."""
    if isinstance(s, str):
        return {"path": s, "lines": None, "key": s}
    path = s["path"]
    lines = s.get("lines")
    key = f"{path}#L{lines}" if lines else path
    return {"path": path, "lines": lines, "key": key}


def parse_lines(spec: str) -> tuple[int, int]:
    a, _, b = spec.partition("-")
    return int(a), int(b or a)


# ── جلب البصمات عبر gh ─────────────────────────────────────────────────────────
def _gh(args: list[str]) -> str | None:
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True,
                             check=True, encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout


def gh_content_sha(repo: str, ref: str, path: str) -> str | None:
    """sha لمسار: ملف=blob sha، مجلد=tree sha."""
    out = _gh(["api", f"repos/{repo}/contents/{path}?ref={ref}",
               "--jq", 'if type=="array" then "DIR" else .sha end'])
    if out is None:
        return None
    val = out.strip()
    if val == "DIR":
        return _gh_tree_sha(repo, ref, path)
    return val or None


def _gh_tree_sha(repo: str, ref: str, path: str) -> str | None:
    parent = str(Path(path).parent).replace("\\", "/")
    parent = "" if parent == "." else parent
    name = Path(path).name
    out = _gh(["api", f"repos/{repo}/contents/{parent}?ref={ref}",
               "--jq", f'.[] | select(.name=="{name}") | .sha'])
    return out.strip() if out else None


def gh_raw(repo: str, ref: str, path: str) -> str | None:
    return _gh(["api", "-H", "Accept: application/vnd.github.raw",
                f"repos/{repo}/contents/{path}?ref={ref}"])


def fetch_sha(repo: str, ref: str, spec: dict) -> str | None:
    """بصمة المصدر: نطاق أسطر ⇒ sha256 للمقطع؛ غير ذلك ⇒ git sha."""
    if spec["lines"]:
        raw = gh_raw(repo, ref, spec["path"])
        if raw is None:
            return None
        lines = raw.splitlines()
        a, b = parse_lines(spec["lines"])
        chunk = "\n".join(lines[a - 1:b])
        digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]
        return f"sha256:{digest}"
    return gh_content_sha(repo, ref, spec["path"])


# ── البيان ─────────────────────────────────────────────────────────────────────
def load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_specs(manifest: dict):
    """يولّد (chapter_file, spec) لكل مصدر بعد التطبيع."""
    for ch in manifest["chapters"]:
        for s in ch["sources"]:
            yield ch["file"], normalize_source(s)


def unique_specs(manifest: dict) -> dict[str, dict]:
    specs = {}
    for _, spec in iter_specs(manifest):
        specs[spec["key"]] = spec
    return specs


def chapters_for_key(manifest: dict, key: str) -> list[str]:
    return sorted({ch for ch, spec in iter_specs(manifest) if spec["key"] == key})


def collect_shas(manifest: dict, ref: str) -> tuple[dict, list]:
    specs = unique_specs(manifest)
    shas, missing = {}, []
    print(f"… جلب بصمات {len(specs)} مصدرًا من {manifest['repo']}@{ref}",
          file=sys.stderr)
    for key, spec in sorted(specs.items()):
        sha = fetch_sha(manifest["repo"], ref, spec)
        if sha is None:
            missing.append(key)
        else:
            shas[key] = sha
    return shas, missing


# ── ملف القفل ──────────────────────────────────────────────────────────────────
def write_lock(manifest: dict, ref: str, shas: dict, version: str | None) -> None:
    lock = {
        "repo": manifest["repo"],
        "ref": ref,
        "covers_version": version if version is not None
        else manifest.get("covers_version"),
        "sources": shas,
    }
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCKFILE, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


# ── (د) حارس البيان دون شبكة ────────────────────────────────────────────────────
def technical_chapters_in_summary() -> set[str]:
    """فصول SUMMARY التي تحت أقسامٍ تقنيّة تستوجب تسجيل مصادرها."""
    import re
    if not SUMMARY.exists():
        return set()
    text = SUMMARY.read_text(encoding="utf-8")
    # نلتقط مسارات الفصول داخل الأجزاء التقنيّة (الأماميّة/الخلفيّة/الأنظمة/مصدر الحقيقة)
    techy = re.findall(r"\]\((src/(?:frontend|backend|systems|sot)/[\w\-/]+\.md)\)",
                       text)
    # SUMMARY يستخدم مسارات نسبيّة بلا بادئة src/ — لذا نعيد التقاطها بنمطين
    rel = re.findall(r"\]\(((?:frontend|backend|systems|sot)/[\w\-/]+\.md)\)", text)
    return {("src/" + p) for p in rel} | set(techy)


def cmd_validate(manifest: dict) -> int:
    errs, warns = [], []
    seen: dict[str, str] = {}
    for ch, spec in iter_specs(manifest):
        if spec["key"] in seen and seen[spec["key"]] != ch:
            pass  # نفس المصدر لفصول متعدّدة مسموح
        seen[spec["key"]] = ch
        if spec["lines"]:
            try:
                a, b = parse_lines(spec["lines"])
                if a < 1 or b < a:
                    errs.append(f"نطاق أسطر غير صالح في {spec['key']}")
            except ValueError:
                errs.append(f"صيغة أسطر غير صالحة: {spec['key']}")
    chapter_files = {ch for ch, _ in iter_specs(manifest)}
    for ch in sorted(chapter_files):
        if not (ROOT / ch).exists():
            errs.append(f"فصلٌ مسجَّل غير موجود على القرص: {ch}")
    # كل فصل تقنيّ في SUMMARY يجب أن يكون مسجَّلًا
    for ch in sorted(technical_chapters_in_summary()):
        if (ROOT / ch).exists() and ch not in chapter_files:
            warns.append(f"فصلٌ تقنيّ غير مسجَّل في sources.yaml: {ch}")

    for w in warns:
        print(f"⚠️ {w}")
    for e in errs:
        print(f"❌ {e}")
    if errs:
        return 1
    print(f"✅ البيان سليم ({len(chapter_files)} فصلًا مسجَّلًا)"
          + (f"، {len(warns)} تحذيرًا" if warns else "") + ".")
    return 1 if warns else 0


# ── (أ) حارس القفل: لا كتم صامت ─────────────────────────────────────────────────
def cmd_guard_lock(manifest: dict, base_path: str, changed_path: str) -> int:
    """يرفض تقدّم بصمةٍ في القفل دون تعديل الفصل المرتبط في نفس الـPR."""
    cur = json.loads(LOCKFILE.read_text(encoding="utf-8")).get("sources", {})
    base_file = Path(base_path)
    if not base_file.exists() or not base_file.read_text(encoding="utf-8").strip():
        print("ℹ️ لا قفل أساس (ملف جديد على الأرجح) — يُتخطّى الحارس.")
        return 0
    base = json.loads(base_file.read_text(encoding="utf-8")).get("sources", {})
    if cur == base:
        print("ℹ️ القفل لم يتغيّر — لا حاجة للحارس.")
        return 0
    advanced = sorted(k for k, v in cur.items() if k in base and base[k] != v)
    added = sorted(k for k in cur if k not in base)
    changed_files = {l.strip().replace("\\", "/")
                     for l in Path(changed_path).read_text(encoding="utf-8").splitlines()
                     if l.strip()}
    offenders = []
    for key in advanced + added:
        chapters = chapters_for_key(manifest, key)
        if not any(c in changed_files for c in chapters):
            offenders.append((key, chapters))
    if offenders:
        print("❌ كتمٌ صامت مرصود: تقدّمت بصماتٌ في القفل دون تعديل فصولها:\n")
        for key, chapters in offenders:
            print(f"   • المصدر `{key}` تقدّم، لكن لم يُعدَّل أيّ من: "
                  f"{', '.join(chapters) or '(لا فصل!)'}")
        print("\nالقاعدة: لا تثبّت بصمةً جديدة (`--update`) إلّا بعد مراجعة الفصل "
              "المرتبط وتعديله فعليًّا. راجع الفصل، عدّله، ثم أعِد --update.")
        return 1
    print(f"✅ الحارس مرّ: كل بصمةٍ تقدّمت ({len(advanced)+len(added)}) رافقها "
          "تعديلُ فصلها.")
    return 0


# ── الفحص الرئيسيّ ──────────────────────────────────────────────────────────────
def cmd_check(manifest: dict, ref: str, as_json: bool) -> int:
    shas, missing = collect_shas(manifest, ref)
    if not LOCKFILE.exists():
        print("⚠️ لا يوجد sources.lock.json — شغّل --update لتوليده أوّلًا.",
              file=sys.stderr)
        return 2
    lock = json.loads(LOCKFILE.read_text(encoding="utf-8"))
    old = lock.get("sources", {})

    changed = [k for k, s in shas.items() if k in old and old[k] != s]
    added = [k for k in shas if k not in old]
    removed = [k for k in old if k not in shas]
    drift_keys = sorted(set(changed) | set(removed))
    affected = sorted({c for k in drift_keys for c in chapters_for_key(manifest, k)})

    report = {
        "drift": bool(drift_keys or missing or added),
        "ref": ref,
        "changed": sorted(changed),
        "added": sorted(added),
        "removed": sorted(removed),
        "missing": sorted(missing),
        "affected_chapters": affected,
        "covers_version": lock.get("covers_version"),
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["drift"] else 0
    if not report["drift"]:
        print(f"✅ الدليل متزامن. ({len(shas)} مصدرًا، نسخة "
              f"{lock.get('covers_version')}، ref={ref})")
        return 0
    print(f"⚠️ انجراف مرصود (ref={ref}) — الدليل قد لا يطابق الكود:\n")
    for title, items in (("📝 مصادر تغيّرت", changed),
                         ("➕ مصادر أُضيفت (سجّلها بـ--update)", added),
                         ("➖ مصادر حُذفت/نُقلت", removed),
                         ("❓ مصادر متعذّر الوصول", missing)):
        if items:
            print(title + ":")
            for p in items:
                print(f"   • {p}")
    if affected:
        print("\n📚 فصول تحتاج مراجعة:")
        for c in affected:
            print(f"   • {c}")
    print("\nبعد مراجعة الفصول وتحديثها، ثبّت الحالة بـ:"
          "\n   python scripts/check_sync.py --update")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="كاشف انجراف دليل المطوّرين وحُرّاسه")
    ap.add_argument("--update", action="store_true",
                    help="ثبّت البصمات الحاليّة (بعد مراجعة الدليل)")
    ap.add_argument("--json", action="store_true", help="تقرير JSON")
    ap.add_argument("--ref", help="تجاوز ref البيان (مثلًا وسم إصدار)")
    ap.add_argument("--set-version", help="مع --update: اكتب covers_version هذا")
    ap.add_argument("--validate", action="store_true",
                    help="حارس بلا شبكة لسلامة البيان")
    ap.add_argument("--guard-lock", action="store_true",
                    help="حارس CI: امنع تقدّم القفل دون تعديل الفصل")
    ap.add_argument("--base", help="مع --guard-lock: ملف قفل الأساس")
    ap.add_argument("--changed-files", help="مع --guard-lock: ملفّ بقائمة الملفّات المعدَّلة")
    args = ap.parse_args()

    manifest = load_manifest()
    ref = args.ref or manifest["ref"]

    if args.validate:
        return cmd_validate(manifest)
    if args.guard_lock:
        if not (args.base and args.changed_files):
            sys.exit("‏--guard-lock يستلزم --base و--changed-files")
        return cmd_guard_lock(manifest, args.base, args.changed_files)
    if args.update:
        shas, missing = collect_shas(manifest, ref)
        write_lock(manifest, ref, shas, args.set_version)
        msg = f"✅ حُدِّث {LOCKFILE.name} ({len(shas)} مصدرًا، ref={ref}"
        msg += f"، نسخة {args.set_version})." if args.set_version else ")."
        if missing:
            msg += f"\n⚠️ مصادر مفقودة لم تُسجَّل: {', '.join(missing)}"
        print(msg)
        return 0
    return cmd_check(manifest, ref, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
