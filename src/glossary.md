# مسرد المصطلحات

| المصطلح | المعنى |
|---------|--------|
| **AST** | الشجرة النحويّة المجرّدة — تمثيل البرنامج بعد التحليل النحوي (`shared/ast/`). |
| **SIR** | Sad Intermediate Representation — تمثيل وسيط بين AST وLLVM (`compiler/src/frontend/`). |
| **SoT** | Single Source of Truth — مصدر الحقيقة الموحّد (`language-truth/`). |
| **`language-truth/`** | مجلد YAML يكتلج بيانات اللغة والقواعد؛ يُولَّد منه الكود والتوثيق. |
| **codegen** | توليد الكود — `scripts/codegen/gen_*.py` تقرأ YAML وتُنتج C++/توثيق. |
| **مُولَّد (generated)** | ملفّات تحت `*/generated/` تُنتَج آليًّا — لا تُحرَّر يدويًّا، لكن متتبَّعة في git. |
| **recursive descent** | المحلل النزوليّ التعاوديّ — كل قاعدة نحويّة دالة `parseXxx()`. |
| **production rule** | قاعدة إنتاج نحويّة في `language-truth/grammar/` (`gr.<area>.<name>`). |
| **`maps_to`** | حقل يربط قاعدة الإنتاج بدالة المحلل الفعليّة (جسر التتبُّع). |
| **Visitor** | نمط الزائر لاستهلاك عقد AST (`ASTVisitor`). |
| **Value** | نوع القيم الموحّد وقت التشغيل (`shared/types/include/value.h`). |
| **goroutine** | خيط خفيف للتزامن؛ يتواصل عبر قنوات (`SadChannel`). |
| **التنفيذ المزدوج** | اشتراط أن تعمل الميزة في المفسّر **والمترجم** بنفس المخرَج (BF-08). |
| **DoD** | Definition of Done — معيار اعتبار التغيير منجَزًا. |
| **worktree** | فرع git في مجلد منفصل يشارك نفس المستودع (`C:/s_lang/temp-brunch/`). |
| **CW-NN / BF-NN / GR-NN** | قواعد كتابة الكود / إصلاح الأخطاء / الحوكمة (مراجع معياريّة). |
| **sad-build** | مُترجِم لغة ص (AST → SIR → LLVM → تنفيذيّ). هدفُ CMake ومُخرَجُه `sad-build.exe`، ويقرأه الـrunner من `build/bin/Debug/`. |
| **sad-run** | المفسّر الشجريّ (`sad-run.exe`) — من `build/bin/Debug/` كذلك: الثنائيّان في **تهيئةٍ واحدة**. |
| **sad** | موزِّع الأوامر (hub) — يُشغّل الأدوات عمليّاتٍ فرعيّة، وليس المفسّر. |
| **~~sadc~~** | اسمٌ **متقاعد**: لا هدفَ يُنتجه اليوم. المترجم هو `sad-build`. |
| **`tests/config.yaml`** | مصدرُ مسارَي الثنائيَّين و`tests_dir` — لا تنسخ ثنائيًّا باسمٍ آخر لأجل الـrunner. |

---
[العودة للمقدّمة](introduction.md)
