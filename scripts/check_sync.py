#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
كاشف انجراف الدليل (drift checker) عن مصادره في مستودع اللغة + حُرّاسه.

يربط sync/sources.yaml كلَّ فصلٍ بمصادره الحقيقيّة في مستودع اللغة. لكل مصدر
بصمةٌ نقارنها بـsync/sources.lock.json:
  - ملفّ/مجلد كامل: بصمة git (blob/tree sha) عبر `gh api .../contents`.
  - نطاق أسطر (تقليل الضجيج): نجلب المحتوى الخام، نقتطع النطاق، ونبصمه sha256.
    هكذا لا يُطلِق تعديلٌ خارج النطاق إنذارًا كاذبًا، ويُرصد «تعفّن» المنطقة الموثَّقة.
  - أسماء المدخلات `{path, names: true}`: نبصم **أسماءَ وأنواعَ** مدخلات المجلّد
    (مرتَّبةً) لا محتواها. هذا النمطُ هو الوحيد الذي يطابق دعوى «هذا المجلّد يحوي
    كذا وكذا» — فبصمةُ الشجرة (tree sha) تنقلب مع أيّ تعديلِ محتوًى داخله فتُنتج
    إنذارًا أسبوعيًّا دائمًا، وهو عينُ الضجيجِ الذي يُسكِت الكاشفَ كلَّه.
    ويُكتب `path: "."` لبصم جذر المستودع (دعاوى خريطة الشجرة).
  - مصدرٌ داخليّ `self:<path>`: يُبصَم من **هذا المستودع** لا من مستودع اللغة، بلا
    شبكة. لأنّ فصولًا (مثل freshness.md) توثّق أدواتِ الدليل نفسِها، فكانت تتعفّن
    عنها بلا كاشف — وقد وقع ذلك فعلًا: وصف الفصلُ سلوكًا نُقض في نفس اليوم.

الأطوار:
  (افتراضيّ)        فحص وتقرير؛ يفشل (1) عند الانجراف.
  --json            تقرير JSON للأتمتة.
  --update          يثبّت البصمات الحاليّة (بعد مراجعة الدليل).
  --ref REF         يتجاوز ref البيان (مثلًا وسم إصدار: v1.2.0) — لربط المزامنة بالإصدارات.
                    تنبيه: البصماتُ المخزّنة أُخذت عند `lock.ref`، فقياسُها عند مرجعٍ سواه
                    يجعل «حُذف/متعذّر» تعني «غير موجودٍ عند ذلك المرجع» لا «أُزيل من اللغة»؛
                    لذا يرفع الفحصُ لافتةً على المعيار حين يختلف المرجعان. ولربط الدليل
                    بإصدارٍ منشور: أعِد البصم عنده (--ref vX --update --set-version X).
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
    """يحوّل مصدرًا (نصّ أو كائن {path, lines|names}) إلى صيغة موحّدة بمفتاح فريد."""
    if isinstance(s, str):
        return {"path": s, "lines": None, "names": False, "key": s}
    path = s["path"]
    lines = s.get("lines")
    names = bool(s.get("names"))
    if names:
        key = f"{path}#names"
    elif lines:
        key = f"{path}#L{lines}"
    else:
        key = path
    return {"path": path, "lines": lines, "names": names, "key": key}


def is_self(spec: dict) -> bool:
    """مصدرٌ داخليّ: يُبصَم من مستودع الدليل نفسِه، لا من مستودع اللغة."""
    return spec["path"].startswith("self:")


def self_path(spec: dict) -> Path:
    return ROOT / spec["path"][len("self:"):]


def parse_lines(spec: str) -> tuple[int, int]:
    a, _, b = spec.partition("-")
    return int(a), int(b or a)


# ── جلب البصمات عبر gh ─────────────────────────────────────────────────────────
def _run(args: list[str]) -> str | None:
    """أمرٌ محلّيّ (git) — يعيد None عند أيّ فشل، فلا يُقرأ العجزُ نجاحًا."""
    try:
        out = subprocess.run(args, capture_output=True, text=True,
                             check=True, encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return out.stdout


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


def gh_entry_names(repo: str, ref: str, path: str) -> str | None:
    """أسماءُ وأنواعُ مدخلات المجلّد مرتَّبةً — لا محتواها."""
    api_path = "" if path in (".", "") else path
    # (AR) `contents` يقتطع عند 1000 مدخلًا **صامتًا** — لا يُخطئ. فقائمةٌ مقتطعةٌ
    #      تُبصَم بصمةً ثابتةً تخضرّ أبدًا. نجعل التجاوزَ «متعذّرًا» لا بصمة.
    out = _gh(["api", f"repos/{repo}/contents/{api_path}?ref={ref}",
               "--jq", 'if type=="array" then (if length >= 1000 then "CAP" '
                       'else ([.[] | .type + ":" + .name] | sort | join("\n")) end) '
                       'else "NOTDIR" end'])
    if out is None:
        return None
    val = out.strip()
    if val == "CAP":
        print(f"⚠️ {path}: تجاوز سقفَ 1000 مدخلٍ في contents API — لم يُقَس.",
              file=sys.stderr)
        return None
    return None if val in ("", "NOTDIR") else val


def _names_digest(listing: str) -> str:
    return "names:" + hashlib.sha256(listing.encode("utf-8")).hexdigest()[:16]


def gh_raw(repo: str, ref: str, path: str) -> str | None:
    return _gh(["api", "-H", "Accept: application/vnd.github.raw",
                f"repos/{repo}/contents/{path}?ref={ref}"])


def _chunk_digest(raw: str, lines_spec: str | None) -> str | None:
    lines = raw.splitlines()
    if lines_spec:
        a, b = parse_lines(lines_spec)
        lines = lines[a - 1:b]
    # (AR) لا مقطعَ ⇒ «متعذّر» يحمرّ، لا بصمةَ خواءٍ تُثبَّت فتخضرّ للأبد.
    #      أربعُ حالاتٍ متباينةٍ كانت تُنتج البصمةَ نفسَها (`e3b0c442…`): ردٌّ فارغٌ
    #      من gh · نطاقٌ خارجَ الملفّ · ملفٌّ صفريّ · ملفٌّ انكمش دون النطاق.
    #      فلو انكمش الملفُّ لاحمرَّ الفحصُ مرّةً ثمّ ثبّته `--update`، ومنذُها
    #      يبقى المصدرُ أخضرَ وهو غيرُ مقيسٍ أصلًا.
    if not lines:
        return None
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]
    return f"sha256:{digest}"


def fetch_self_sha(spec: dict) -> str | None:
    """بصمةُ مصدرٍ داخليّ من قرص هذا المستودع — بلا شبكة."""
    p = self_path(spec)
    if spec["names"]:
        # (AR) الوعدُ في freshness.md أن نستبعدَ ما لا يخزّنه git. مسحُ القرص
        #      بقائمةِ استثناءاتٍ منثورةٍ لا يفي به: قِيس أنّ جذرَ مستودعِ اللغة
        #      43 مدخلًا في git و70 على القرص (`book/` · `.venv` · بل ملفّاتُ
        #      خطوةِ الحارسِ نفسِها). فنشتقُّ الحقيقةَ من git لا من القرص.
        if not p.is_dir():
            return None
        # (AR) القرصُ يحوي ما لا يحويه git (`.git` · `__pycache__` · مخلّفاتُ بناء)،
        #      فبصمةٌ تشملها تنقلب بلا واقعةٍ في المستودع — ضجيجٌ غيرُ حتميّ.
        #      نستبعدها لتبقى البصمةُ دالّةً على الشجرة المُودَعة وحدها.
        skip = {".git", "__pycache__", ".mypy_cache", ".pytest_cache"}
        rel = spec["path"][len("self:"):].strip("/")
        out = _run(["git", "-C", str(ROOT), "ls-tree", "HEAD",
                    (rel + "/") if rel else "./"])
        if out is not None:
            listed = []
            for line in out.splitlines():
                if not line.strip():
                    continue
                meta, _, name = line.partition("\t")
                kind = meta.split()[1]
                listed.append(("dir:" if kind == "tree" else "file:")
                              + Path(name).name)
            return _names_digest("\n".join(sorted(listed))) if listed else None
        entries = sorted(("dir:" if c.is_dir() else "file:") + c.name
                         for c in p.iterdir() if c.name not in skip)
        # (AR) مجلّدٌ فارغ ⇒ None كجانب github تمامًا (git لا يخزّن مجلّدًا فارغًا)،
        #      فلا نسجّل «بصمةَ خواء» تُقرأ نجاحًا.
        return _names_digest("\n".join(entries)) if entries else None
    if not p.is_file():
        return None
    return _chunk_digest(p.read_text(encoding="utf-8"), spec["lines"])


def fetch_sha(repo: str, ref: str, spec: dict) -> str | None:
    """بصمة المصدر: أسماءُ مدخلات ⇒ names؛ نطاقُ أسطر ⇒ sha256؛ غيرُهما ⇒ git sha."""
    if is_self(spec):
        return fetch_self_sha(spec)
    if spec["names"]:
        listing = gh_entry_names(repo, ref, spec["path"])
        return None if listing is None else _names_digest(listing)
    if spec["lines"]:
        raw = gh_raw(repo, ref, spec["path"])
        if raw is None:
            return None
        return _chunk_digest(raw, spec["lines"])
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
def derived_version(repo: str, ref: str) -> str | None:
    """`dev@<إيداع>` مشتقًّا من المرجعِ البعيد — لا منسوخًا بيدٍ فيتقادم."""
    out = _run(["git", "ls-remote", f"https://github.com/{repo}.git", ref])
    if not out or not out.split():
        return None
    return f"{ref}@{out.split()[0][:8]}"


def write_lock(manifest: dict, ref: str, shas: dict, version: str | None) -> None:
    # (AR) الفصلُ يقول إنّ `covers_version` «يسمّي الإيداعَ الذي قِيست عنده
    #      البصمات». فلا يُنسخ من البيان — يُشتقّ. المكتوبُ بيدٍ صادقٌ اليومَ
    #      بالمصادفة، ولا شيءَ يمنع كذبَه غدًا (عددٌ منثورٌ نسخةً ثانيةً لواقعة).
    auto = None if version is not None else derived_version(manifest["repo"], ref)
    lock = {
        "repo": manifest["repo"],
        "ref": ref,
        "covers_version": version if version is not None
        else (auto or manifest.get("covers_version")),
        "sources": shas,
    }
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCKFILE, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


# ── (د) حارس البيان دون شبكة ────────────────────────────────────────────────────
# (AR) الأجزاءُ التي تستوجب تسجيلَ المصادر. كانت أربعةً (`frontend` · `backend` ·
#      `systems` · `sot`) فبقيت `architecture/` و`getting-started/` و`contributing/`
#      **خارجَ المظلّة كلّيًّا** — وهي التي تحمل دعاوى أوامرَ يُشغّلها القارئ
#      (`runner.py`، مسارُ البناء، شجرةُ المستودع)، فتعفّنت بلا كاشف. النطاقُ الآن
#      كلُّ فصلٍ في قسمٍ من الأقسام السبعة؛ وصفحاتُ الجذر (`introduction` ·
#      `glossary` · `status` · `SUMMARY`) خارجه عمدًا: دعاواها عن الدليلِ نفسِه
#      لا عن اللغة، ومنها ما يُسجَّل طوعًا حين يحمل دعوى مقيسة.
GUARDED_SECTIONS = ("frontend|backend|systems|sot|"
                    "architecture|getting-started|contributing")


def technical_chapters_in_summary() -> set[str]:
    """فصول SUMMARY التي تحت أقسامٍ محروسة تستوجب تسجيل مصادرها."""
    import re
    if not SUMMARY.exists():
        return set()
    text = SUMMARY.read_text(encoding="utf-8")
    techy = re.findall(r"\]\((src/(?:" + GUARDED_SECTIONS + r")/[\w\-/]+\.md)\)",
                       text)
    # SUMMARY يستخدم مسارات نسبيّة بلا بادئة src/ — لذا نعيد التقاطها بنمطين
    rel = re.findall(r"\]\(((?:" + GUARDED_SECTIONS + r")/[\w\-/]+\.md)\)", text)
    return {("src/" + p) for p in rel} | set(techy)


def self_drift_errors(manifest: dict) -> list[str]:
    """تعفّنُ مصادرِ `self:` مقيسًا بلا شبكة — بوّابةُ PR لا كاشفٌ أسبوعيّ."""
    if not LOCKFILE.exists():
        # (AR) لا تُرجِع «سليم» لغيابِ ما تقيسُ به. حذفُ ملفٍّ واحدٍ كان يُطفئ
        #      البوّابةَ صامتةً وخضراء — وهو عينُ «الأخضرُ يعني لم يُقَس».
        if any(is_self(s) for s in unique_specs(manifest).values()):
            return ["لا يوجد sources.lock.json — فلا يمكن قياسُ تعفّنِ مصادر "
                    "`self:` المسجَّلة. شغّل `--update` أوّلًا."]
        return []
    locked = json.loads(LOCKFILE.read_text(encoding="utf-8")).get("sources", {})
    out = []
    for key, spec in sorted(unique_specs(manifest).items()):
        if not is_self(spec) or key not in locked:
            continue
        cur = fetch_self_sha(spec)
        if cur is None or cur == locked[key]:
            continue
        chapters = ", ".join(chapters_for_key(manifest, key)) or "—"
        out.append(f"مصدرٌ داخليّ تغيّر ولم تُثبَّت بصمتُه: {key}\n"
                   f"     راجِع وعدِّل: {chapters}‏ ثمّ شغّل "
                   f"`python scripts/check_sync.py --update`.")
    return out


def cmd_validate(manifest: dict) -> int:
    errs, warns = [], []
    seen: dict[str, str] = {}
    for ch, spec in iter_specs(manifest):
        if spec["key"] in seen and seen[spec["key"]] != ch:
            pass  # نفس المصدر لفصول متعدّدة مسموح
        seen[spec["key"]] = ch
        if spec["names"] and spec["lines"]:
            errs.append(f"مصدرٌ يجمع `names` و`lines` معًا (متعارضان): {spec['key']}")
        if is_self(spec):
            p = self_path(spec)
            if spec["names"] and not p.is_dir():
                errs.append(f"مصدرٌ داخليّ `names` ليس مجلّدًا: {spec['key']}")
            elif not spec["names"] and not p.is_file():
                errs.append(f"مصدرٌ داخليّ غير موجود: {spec['key']}")
            elif not spec["names"] and fetch_self_sha(spec) is None:
                errs.append("مصدرٌ داخليّ نطاقُه خارجَ الملفّ (لا شيءَ يُقاس): "
                            f"{spec['key']}")
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

    # (AR) مصادرُ `self:` لا تحتاج شبكة، فيمكن قياسُ تعفّنها **في نفس الـPR** لا أن
    #      ينتظر الأسبوعيّ. بدون هذا كان النمطُ الجديد كاشفًا أسبوعيًّا لا بوّابةَ PR:
    #      يُعدَّل `check_sync.py` وحده فيمرّ الـPR أخضرَ والفصلُ الذي يصفه متعفّن.
    errs.extend(self_drift_errors(manifest))

    for w in warns:
        print(f"⚠️ {w}")
    for e in errs:
        print(f"❌ {e}")
    if errs:
        return 1
    # (AR) لا تُنهِ سجلًّا فاشلًا بسطرِ «✅». مَن يمسح سجلَّ CI بعينه يقرأ آخرَ
    #      سطرٍ حكمًا؛ فكان «✅ البيان سليم … 1 تحذيرًا» يُقرأ نجاحًا ورمزُه 1.
    if warns:
        print(f"❌ البيانُ ناقص: {len(chapter_files)} فصلًا مسجَّلًا، "
              f"و{len(warns)} فصلًا محروسًا بلا مصادر — فشل.")
        return 1
    print(f"✅ البيان سليم ({len(chapter_files)} فصلًا مسجَّلًا).")
    return 0


# ── (أ) حارس القفل: لا كتم صامت ─────────────────────────────────────────────────
def cmd_guard_lock(manifest: dict, base_path: str, changed_path: str,
                   base_manifest_path: str | None = None) -> int:
    """يرفض تقدّمَ بصمةٍ **أو إسقاطَها** دون تعديل الفصل المرتبط في نفس الـPR."""
    if not LOCKFILE.exists():
        print("❌ لا يوجد sync/sources.lock.json — الحارسُ لم يُقَس. "
              "شغّل `--update` أوّلًا.")
        return 1
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
    # (AR) القاعدة: **كلّ** فصلٍ يستشهد بالمصدر يجب أن يُعدَّل، لا أيّ فصلٍ منها.
    #      المفتاحُ المشترك (`scripts/codegen` بين codegen.md وphilosophy.md مثلًا)
    #      كان يمرّ بتعديل أحدهما فَيَسِمُ الآخرَ طازجًا دون أن يقرأه أحد — أي أنّ الحارسَ
    #      نفسَه كان يكتم ما بُني لِيَكشِفَه. (عددُ المفاتيح المشتركة يُشتقّ من
    #      البيان عند التشغيل — لا يُكتب هنا رقمًا يتقادم.)
    # (AR) الإسقاطُ كتمٌ صامتٌ أيضًا، من البابِ المقابل: بدل تقديمِ البصمةِ بلا
    #      مراجعة، إزالتُها بلا مراجعة. إسقاطُ مصدرٍ من البيان ثمّ `--update`
    #      كان يقتل الكاشفَ لفصولٍ كاملةٍ والبوّابتان خضراوان — قِيس بإسقاط
    #      `.#names` فمرّ الحارسُ بـ«0 بصمةٍ تقدّمت» وثلاثةُ فصولٍ فقدت دعواها.
    dropped = sorted(k for k in base if k not in cur)
    base_manifest = None
    if base_manifest_path:
        raw = Path(base_manifest_path).read_text(encoding="utf-8")
        if raw.strip():
            base_manifest = yaml.safe_load(raw)
    offenders = []
    for key in advanced + added:
        chapters = chapters_for_key(manifest, key)
        untouched = [c for c in chapters if c not in changed_files]
        if untouched or not chapters:
            offenders.append((key, chapters, untouched))
    for key in dropped:
        # (AR) الفصولُ تُقرأ من **بيانِ الأساس**: المفتاحُ المُسقَط لا أثرَ له في
        #      البيان الحاليّ، فقياسُه عليه يعطي قائمةً فارغةً دائمًا.
        if base_manifest is None:
            offenders.append((f"{key} (أُسقِط)", [],
                              ["<بيانُ الأساس غير مُمرَّر — تعذّر القياس>"]))
            continue
        was = chapters_for_key(base_manifest, key)
        untouched = [c for c in was if c not in changed_files]
        if untouched or not was:
            offenders.append((f"{key} (أُسقِط)", was, untouched))
    if offenders:
        print("❌ كتمٌ صامت مرصود: تغيّرت بصماتٌ في القفل دون تعديل فصولها:\n")
        for key, chapters, untouched in offenders:
            if not chapters:
                print(f"   • المصدر `{key}` تغيّر، ولا فصلَ يستشهد به أصلًا!")
                continue
            shared = [c for c in chapters if c not in untouched]
            print(f"   • المصدر `{key}` تغيّر، ولم يُعدَّل: "
                  f"{', '.join(untouched)}")
            if shared:
                print(f"     (مشتركٌ مع فصولٍ عُدّلت: "
                      f"{', '.join(shared)} — تعديلُ أحدها لا يُبرّئُ البقية)")
        print("\nالقاعدة: لا تثبّت بصمةً جديدة (`--update`) إلّا بعد مراجعة الفصل "
              "المرتبط وتعديله فعليًّا. راجع الفصل، عدّله، ثم أعِد --update.")
        return 1
    print(f"✅ الحارس مرّ: كل بصمةٍ تقدّمت ({len(advanced)+len(added)}) "
          f"أو أُسقِطت ({len(dropped)}) رافقها تعديلُ **كلّ** فصلٍ يستشهد بها.")
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

    # (AR) البصماتُ المخزّنة أُخذت عند `lock["ref"]`. قياسُها عند مرجعٍ آخر
    #      يقارن شيئًا بشيءٍ سواه: مسارٌ لم يكن قد وُجد بعدُ عند وسمٍ قديم
    #      يُقرأ «حُذف». (قِيس: v1.0.0 وسمُ 2026-03-09، وهو قبل `language-truth/`
    #       و`scripts/codegen`، فكان التقريرُ الأسبوعيّ يعلن حذفَ 30 مسارًا
    #       وتعذّرَ 47، وكلّها قائمةٌ سليمةٌ على dev. القضيّة #1 شاهدُها.)
    lock_ref = lock.get("ref")
    if lock_ref and lock_ref != ref:
        print(f"⚠️ المرجع المقيس `{ref}` يخالف مرجع القفل `{lock_ref}`.\n"
              f"   «حُذف» و«متعذّر الوصول» أدناه تعني «غير موجودٍ عند `{ref}`» "
              f"لا «أُزيل من اللغة».\n"
              f"   لقياس تعفّنٍ حقيقيّ: قِس عند مرجع القفل (--ref {lock_ref})، "
              f"أو أعِد البصم عند `{ref}` (--ref {ref} --update).\n",
              file=sys.stderr)

    changed = [k for k, s in shas.items() if k in old and old[k] != s]
    added = [k for k in shas if k not in old]
    removed = [k for k in old if k not in shas]
    drift_keys = sorted(set(changed) | set(removed))
    affected = sorted({c for k in drift_keys for c in chapters_for_key(manifest, k)})

    report = {
        "drift": bool(drift_keys or missing or added),
        "ref": ref,
        "lock_ref": lock_ref,
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
    ap.add_argument("--base-manifest",
                    help="مع --guard-lock: بيانُ الأساس (لقياس المفاتيح المُسقَطة)")
    args = ap.parse_args()

    manifest = load_manifest()
    ref = args.ref or manifest["ref"]

    if args.validate:
        return cmd_validate(manifest)
    if args.guard_lock:
        if not (args.base and args.changed_files):
            sys.exit("‏--guard-lock يستلزم --base و--changed-files")
        return cmd_guard_lock(manifest, args.base, args.changed_files,
                              args.base_manifest)
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
