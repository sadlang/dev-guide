#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
كاشف انجراف الدليل (drift checker) عن مصادره في مستودع اللغة.

يقرأ sync/sources.yaml، ويجلب بصمة (sha) كل مصدر من المستودع الرئيسيّ عبر
`gh api`، ثم يقارنها بالبصمات المحفوظة في sync/sources.lock.json:
  - إن تغيّر مصدرٌ ما ⇒ الفصول المرتبطة به «منجرفة» وتحتاج مراجعة.
  - الخروج برمز 1 عند وجود انجراف (ليكسر CI/المهمة المجدولة).
  - --update يعيد توليد ملف القفل بالبصمات الحاليّة (بعد مراجعة الدليل).

لا يتطلّب استنساخ المستودع: يعتمد على REST عبر gh (contents API) الذي يعيد
sha لكل ملف أو مجلد (git tree sha)، فيكشف أي تغيّر تحت المسار.

الاستعمال:
    python scripts/check_sync.py            # فحص وتقرير (يفشل عند الانجراف)
    python scripts/check_sync.py --update   # تحديث القفل بعد المراجعة
    python scripts/check_sync.py --json      # تقرير JSON (للأتمتة)
"""
from __future__ import annotations

import argparse
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


def gh_content_sha(repo: str, ref: str, path: str) -> str | None:
    """يعيد sha لمسار (ملف=blob sha، مجلد=tree sha) أو None إن غاب."""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}",
             "--jq", "if type==\"array\" then \".\" else .sha end"],
            capture_output=True, text=True, check=True, encoding="utf-8",
        )
    except subprocess.CalledProcessError:
        return None
    val = out.stdout.strip()
    if val == ".":
        # مجلد: contents يعيد مصفوفة بلا sha موحّد ⇒ استعمل sha شجرة git
        return _gh_tree_sha(repo, ref, path)
    return val or None


def _gh_tree_sha(repo: str, ref: str, path: str) -> str | None:
    """sha لشجرة مجلد: نأخذه من قائمة محتويات المجلد الأب."""
    parent = str(Path(path).parent).replace("\\", "/")
    parent = "" if parent == "." else parent
    name = Path(path).name
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{parent}?ref={ref}",
             "--jq", f'.[] | select(.name=="{name}") | .sha'],
            capture_output=True, text=True, check=True, encoding="utf-8",
        )
    except subprocess.CalledProcessError:
        return None
    return out.stdout.strip() or None


def load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_shas(manifest: dict) -> tuple[dict, list]:
    """يجلب بصمات كل المصادر الفريدة. يعيد (خريطة path→sha، قائمة المفقودة)."""
    repo, ref = manifest["repo"], manifest["ref"]
    paths = sorted({s for ch in manifest["chapters"] for s in ch["sources"]})
    shas, missing = {}, []
    print(f"… جلب بصمات {len(paths)} مصدرًا من {repo}@{ref}", file=sys.stderr)
    for p in paths:
        sha = gh_content_sha(repo, ref, p)
        if sha is None:
            missing.append(p)
        else:
            shas[p] = sha
    return shas, missing


def build_lock(manifest: dict, shas: dict) -> dict:
    return {
        "repo": manifest["repo"],
        "ref": manifest["ref"],
        "covers_version": manifest.get("covers_version"),
        "sources": shas,
    }


def write_lock(lock: dict) -> None:
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCKFILE, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def chapters_for_source(manifest: dict, src: str) -> list[str]:
    return [ch["file"] for ch in manifest["chapters"] if src in ch["sources"]]


def main() -> int:
    ap = argparse.ArgumentParser(description="كاشف انجراف دليل المطوّرين")
    ap.add_argument("--update", action="store_true",
                    help="حدّث ملف القفل بالبصمات الحاليّة (بعد مراجعة الدليل)")
    ap.add_argument("--json", action="store_true", help="تقرير JSON")
    args = ap.parse_args()

    manifest = load_manifest()
    shas, missing = collect_shas(manifest)

    if args.update:
        write_lock(build_lock(manifest, shas))
        msg = f"✅ حُدِّث {LOCKFILE.name} ({len(shas)} مصدرًا)."
        if missing:
            msg += f"\n⚠️ مصادر مفقودة لم تُسجَّل: {', '.join(missing)}"
        print(msg)
        return 0

    if not LOCKFILE.exists():
        print("⚠️ لا يوجد sources.lock.json — شغّل --update لتوليده أوّلًا.",
              file=sys.stderr)
        return 2

    with open(LOCKFILE, encoding="utf-8") as f:
        lock = json.load(f)
    old = lock.get("sources", {})

    changed = [p for p, s in shas.items() if old.get(p) != s]
    added = [p for p in shas if p not in old]
    removed = [p for p in old if p not in shas]
    drift_sources = sorted(set(changed) | set(removed))

    affected = sorted({c for src in drift_sources
                       for c in chapters_for_source(manifest, src)})

    report = {
        "drift": bool(drift_sources or missing),
        "changed": sorted(set(changed) - set(added)),
        "added": sorted(added),
        "removed": sorted(removed),
        "missing": sorted(missing),
        "affected_chapters": affected,
        "covers_version": manifest.get("covers_version"),
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["drift"] else 0

    if not report["drift"]:
        print(f"✅ الدليل متزامن. ({len(shas)} مصدرًا، نسخة "
              f"{manifest.get('covers_version')})")
        return 0

    print("⚠️ انجراف مرصود — الدليل قد لا يطابق الكود:\n")
    if report["changed"]:
        print("📝 مصادر تغيّرت:")
        for p in report["changed"]:
            print(f"   • {p}")
    if report["added"]:
        print("➕ مصادر أُضيفت (سجّلها بـ--update):")
        for p in report["added"]:
            print(f"   • {p}")
    if report["removed"]:
        print("➖ مصادر حُذفت/نُقلت:")
        for p in report["removed"]:
            print(f"   • {p}")
    if report["missing"]:
        print("❓ مصادر متعذّر الوصول إليها:")
        for p in report["missing"]:
            print(f"   • {p}")
    if affected:
        print("\n📚 فصول تحتاج مراجعة:")
        for c in affected:
            print(f"   • {c}")
    print("\nبعد مراجعة الفصول وتحديثها، ثبّت الحالة بـ:"
          "\n   python scripts/check_sync.py --update")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
