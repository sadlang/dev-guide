# إعداد البيئة والبناء

> **ماذا ستتعلّم:** كيف تجلب المستودع، تهيّئ الأدوات، وتبني المفسّر والمترجم.

## المتطلبات
- **C++17** ومُصرِّف حديث (MSVC على Windows، أو Clang/GCC).
- **CMake ≥ 3.20**.
- **LLVM 18** — *اختياريّ*، للمترجم `sadc` فقط (`ENABLE_LLVM_BACKEND=ON`).
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
cmake --build build --config Debug   --target sad     # المفسّر (أسرع)
cmake --build build --config Release --target sadc    # المترجم (LLVM)
cmake --build build --config Debug                    # كل شيء
```

> ⚠️ **فخّان مهمّان** (مذكوران في تعليمات المشروع):
> - هدف `sadc` قد يُنتج `sad-build.exe` — انسخه إلى `sadc.exe` قبل `runner.py` وإلا فنتائج المترجم بائتة.
> - الـrunner يقرأ مفسّر **Debug** ومترجم **Release** — أعد بناء التهيئتين معًا.

## التشغيل
```powershell
.\build\bin\Debug\sad.exe examples\test_simple.ص       # تفسير
.\build\bin\Release\sadc.exe examples\test_simple.ص    # ترجمة لملف تنفيذيّ
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
