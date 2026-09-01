# إعداد البيئة والبناء

> **ماذا ستتعلّم:** كيف تجلب المستودع، تهيّئ الأدوات، وتبني المفسّر والمترجم.

## المتطلبات
- **C++17** ومُصرِّف حديث (MSVC على Windows، أو Clang/GCC).
- **CMake ≥ 3.20**.
- **LLVM 18** — *اختياريّ*، للمترجم `sad-build` فقط (`ENABLE_LLVM_BACKEND=ON`).
- **Python 3** — لمولّدات الكود (`scripts/codegen/gen_*.py`) و`runner.py`.
- **Git + GPG** — للمساهمة (الفروع المحميّة تشترط توقيع GPG).

## الجلب
```bash
git clone https://github.com/sadlang/s-programming-language.git
cd s-programming-language
```

## البناء (PowerShell على Windows)
```powershell
cmake -S . -B build                                   # تهيئة أولى
cmake --build build --config Debug   --target sad-run    # المفسّر (أسرع)
cmake --build build --config Release --target sad-build  # المترجم (LLVM)
cmake --build build --config Debug                    # كل شيء
```

> ⚠️ **ثلاثة فخاخ:**
> - **`sadc.exe` اسمٌ متقاعد — لا يُنتجه أيّ هدف.** اسمُ الهدف مُوحَّدٌ مع اسم
>   المُخرَج: `sad-run` ⇒ `sad-run.exe`، و`sad-build` ⇒ `sad-build.exe`
>   ([`tests/config.yaml`](https://github.com/sadlang/s-programming-language/blob/dev/tests/config.yaml)).
>   فلا تنسخ ثنائيًّا باسمٍ آخر لأجل `runner.py` — فهو يقرأ المسارَين من ذلك الملفّ.
> - `sad.exe` ليس المفسّر بل **موزِّع أوامرٍ (hub)** يُشغّل الأدواتِ عمليّاتٍ فرعيّة؛
>   المفسّرُ الفعليّ `sad-run.exe`، فاستدعِه مباشرةً.
> - الـrunner يقرأ تهيئتَي الثنائيَّين من `tests/config.yaml` — أعد بناءهما معًا
>   حتّى لا تقيس ثنائيًّا بائتًا.

## التشغيل
```powershell
.\build\bin\Debug\sad-run.exe examples\test_simple.ص       # تفسير
.\build\bin\Release\sad-build.exe examples\test_simple.ص  # ترجمة لملف تنفيذيّ
```

## الاختبارات
الاختبارات **معطّلة افتراضيًّا**؛ فعّلها بـ`-DBUILD_TESTS=ON`. للتنفيذ المزدوج (مفسّر + مترجم) استخدم `runner.py`:
```bash
python runner.py --level P0      # الحزمة الأساسيّة
python runner.py --level P1      # المطلوبة قبل أي PR (لا تراجع)
```

## توليد الكود من مصدر الحقيقة
بعد تعديل أي YAML في `language-truth/`:
```bash
python scripts/codegen/gen_keywords.py        # مثال: الكلمات المفتاحيّة
python scripts/codegen/gen_parser_grammar_docs.py   # توثيق القواعد
```
> راجع [توليد الكود](../sot/codegen.md).

---
**اقرأ بعده:** [أوّل مساهمة](first-contribution.md).
