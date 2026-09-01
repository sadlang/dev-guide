# إعداد البيئة والبناء

> **ماذا ستتعلّم:** كيف تجلب المستودع، تهيّئ الأدوات، وتبني المفسّر والمترجم.

> 📎 المصدر: [`CMakeLists.txt`](https://github.com/sadlang/s-programming-language/blob/dev/CMakeLists.txt) ·
> [`tests/config.yaml`](https://github.com/sadlang/s-programming-language/blob/dev/tests/config.yaml)

## المتطلبات
- **C++17** ومُصرِّف حديث (MSVC على Windows، أو Clang/GCC).
- **CMake ≥ 3.15** — هذا ما يشترطه `cmake_minimum_required` فعلًا، لا 3.20.
- **LLVM 18** — للمترجم `sad-build`. الخيار `ENABLE_LLVM_BACKEND` **افتراضيّه
  `ON`**، فلا تحتاج تمريره. ودقّق: هدفُ `sad-build` **يُعرَّف داخل**
  `if(ENABLE_LLVM_BACKEND AND LLVM_FOUND)` في `apps/CMakeLists.txt` — فبلا LLVM
  لا يوجد الهدفُ أصلًا، ويسقط `x.py build` معه، ولا يُنتَج
  `build/bin/Debug/sad-build.exe` الذي يشترطه `tests/config.yaml` **أبدًا**.
  البديلُ الحقيقيّ هو الهدفُ المستقلّ **`sad-build-native`** (المترجم النحيل، بلا
  LLVM، في كلّ التهيئات) — راجع [فصل LLVM](../backend/llvm.md) و[الخلفيّة
  الأصليّة](../backend/native.md). فإن لم تنوِ استعمالَ الخلفيّة الأصليّة،
  اعتبِر LLVM **شرطًا** لا خيارًا.
- **Python 3** — لمولّدات الكود (`scripts/codegen/gen_*.py`) و`tests/runner.py`.
- **Git + GPG** — للمساهمة (الفروع المحميّة تشترط توقيع GPG).

## الجلب
```bash
git clone https://github.com/sadlang/s-programming-language.git
cd s-programming-language
```

## البناء
الطريق المُوصى به هو البوّابة الموحّدة `x.py` — تبني المحرّكين **معًا لكلّ تهيئة**،
فلا تقع في اختلاف التهيئتين الموصوف تحت:
```bash
python x.py build          # بناء المحرّكين
python x.py test           # بناء + تحقّق + تشغيل الـrunner
python x.py gen            # توليد المصدر من language-truth/
```
(الأوامر الأخرى: `configure` · `verify` · `conformance` · `clean`.)

وإن بنيتَ بـCMake مباشرةً (PowerShell على Windows):
```powershell
cmake -S . -B build                                 # تهيئة أولى
cmake --build build --config Debug --target sad-run    # المفسّر
cmake --build build --config Debug --target sad-build  # المترجم
cmake --build build --config Debug                  # كل شيء
```

> ⚠️ **فخاخُ البناء:**
> - **ابنِ الاثنين في تهيئةٍ واحدة، وأعِد بناءهما معًا.** `tests/config.yaml` يقرأ
>   المسارَين من **`build/bin/Debug/`** كليهما. فإن بنيتَ `sad-build` في `Release`
>   لم يجده الـrunner، وإن أعدتَ بناءَ أحدهما وحدَه قِستَ ثنائيًّا بائتًا. وهذه
>   بعينها عثرةُ «مفسّر Debug + مترجم Release» التي **يقول تعليقُ
>   `tests/config.yaml` نفسِه** إنّها أُزيلت جذريًّا في `cmake/llvm.cmake`؛
>   لا تُعِدها بيدك.
> - **`sadc.exe` اسمٌ متقاعد — لا يُنتجه أيّ هدف.** اسمُ الهدف مُوحَّدٌ مع اسم
>   المُخرَج: `sad-run` ⇒ `sad-run.exe`، و`sad-build` ⇒ `sad-build.exe`.
>   فلا تنسخ ثنائيًّا باسمٍ آخر لأجل الـrunner — فهو يقرأ المسارَين من ذلك الملفّ.
> - `sad.exe` ليس المفسّر بل **موزِّع أوامرٍ (hub)** يُشغّل الأدواتِ عمليّاتٍ فرعيّة؛
>   المفسّرُ الفعليّ `sad-run.exe`، فاستدعِه مباشرةً.

## التشغيل
الأمثلة الفعليّة تحت `examples/` بأسماء عربيّة مرقّمة (`01_مرحبا.ص` … `07_مكوّن_مركّب.ص`):
```powershell
.\build\bin\Debug\sad-run.exe examples\01_مرحبا.ص      # تفسير
.\build\bin\Debug\sad-build.exe examples\01_مرحبا.ص    # ترجمة لملف تنفيذيّ
```

## الاختبارات
الاختبارات **معطّلة افتراضيًّا** (`option(BUILD_TESTS ... OFF)`)؛ فعّلها بـ`-DBUILD_TESTS=ON`.
للتنفيذ المزدوج (مفسّر + مترجم) استخدم **`tests/runner.py`** — لا يوجد `runner.py`
في جذر المستودع، وهذا هو الاستدعاء الذي يستعمله CI نفسه:
```bash
python tests/runner.py --level P0      # الحزمة الأساسيّة
python tests/runner.py --level P1      # المطلوبة قبل أي PR (لا تراجع)
```
(و`python x.py test` يبني المحرّكين ثمّ يستدعي هذا الـrunner نفسَه — استعمِله حين
تريد البناءَ والقياسَ في خطوة، والاستدعاءَ المباشرَ حين يكون البناءُ حاضرًا.)

## توليد الكود من مصدر الحقيقة
بعد تعديل أي YAML في `language-truth/`:
```bash
python x.py gen                                    # كلُّ المولّدات دفعةً واحدة
python scripts/codegen/gen_keywords.py             # أو مولِّدٌ بعينه
python scripts/codegen/gen_parser_grammar_docs.py  # توثيق القواعد
```
> راجع [توليد الكود](../sot/codegen.md).

---
**اقرأ بعده:** [خريطة المستودع](repo-map.md).
