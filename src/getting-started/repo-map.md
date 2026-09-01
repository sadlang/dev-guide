# خريطة المستودع

> **ماذا ستتعلّم:** أين يعيش كل شيء في `sadlang/s-programming-language`.

> 📎 مقيسٌ على `dev` — الأسماء والأعداد أدناه من شجرة المستودع نفسها لا من الذاكرة.

```
s-programming-language/
├── x.py                    ← البوّابة الموحّدة: سبعةُ أوامر (build · test · gen ·
│                             verify · configure · conformance · clean)
├── shared/                 ← النواة المشتركة
│   ├── lexer/              ← المحلل المعجمي + Token + Position
│   ├── parser/             ← المحلل النحوي (recursive descent)
│   ├── ast/                ← عقد شجرة AST + ASTVisitor
│   ├── types/              ← Value (نوع القيم الموحّد) + SadType
│   └── errors/             ← نظام الأخطاء + رموزها
├── interpreter/            ← المفسّر الشجريّ (InterpreterCore + visitors + builtins)
├── compiler/               ← المترجم: AST → SIR → LLVM IR → تنفيذيّ
│   ├── src/frontend/       ← SIRBuilder + sir_types.h (opcodes الملكية)
│   ├── src/backend/llvm/   ← LLVMCodeGen + builders
│   └── include/backend/native/
│                            ← الخلفيّة الأصليّة (بلا LLVM)
├── stdlib/                 ← المكتبة القياسية: وحدات `.ص` في الجذر + مجلّدات دعم C++
├── features/               ← أنظمةٌ كبرى مستقلّة (منها SadUI للرسومات)
├── runtime/                ← ABI/FFI المستقلّ + الوضع الحرّ (freestanding)
├── tools/                  ← ١٥ مجلّدَ أدوات (sad-build · sad · lsp · repl …)
├── language-truth/         ← ⭐ مصدر الحقيقة الموحّد (YAML)
│   ├── keywords.yaml · operators.yaml · types.yaml · directives.yaml
│   ├── builtins/ · errors/ · grammar/   ← قواعد الإنتاج (SoT)
│   └── _schemas/                        ← مخطّطات JSON للتحقّق
├── scripts/codegen/        ← gen_*.py (تقرأ YAML وتُنتج C++/توثيق)
├── docs/                   ← توثيق (incl. parser_rule/_generated المُولَّد)
├── examples/               ← أمثلة `.ص` مرقّمة (`01_مرحبا.ص` … `07_مكوّن_مركّب.ص`)
├── tests/                  ← `runner.py` · `config.yaml` · `framework/` · `metrics/`
│   └── behavior/           ← ⟵ هنا تعيش حِزَم `.ص` الستّ (انظر الجدول أدناه)
├── _bmad-output/           ← نظام الحوكمة (سياسات/ستوريات/قرارات)
└── .github/skills/         ← مهارات الوكلاء (sad-lang-dev …)
```


### ماذا في `stdlib/` و`features/` و`tests/behavior/`
هذه القوائمُ **خارج كتلة الكود عمدًا**: كتلُ الكود تُعرَض LTR (`theme/rtl.css`)،
فينقلبُ فيها ترتيبُ أيّ سلسلةٍ عربيّةٍ أمامَ عين القارئ.

| المجلّد | ما فيه |
|------|------|
| `stdlib/` — وحدات `.ص` | رياضيات · نصوص · مصفوفات · خرائط · ملفات · شبكات · جيسون · وقت |
| `stdlib/` — مجلّدات دعم C++ (١٧) | `io` · `math` · `string` · `json` · `xml` · `database` · `filesystem` · `image` · `include` · `low_level` · `platform` · `system` · `test` · `freestanding` · `إضافات` · `نص` · `ويب` |
| `features/` | `graphics` (SadUI: التخطيط ومفاتيح الخصائص) · `network` — **الرسومات ليست في `stdlib`** |
| `tools/` (١٥) | `analyze` · `apk_builder` · `build` · `check` · `compiler` (واجهة `sad-build`) · `formatter` · `hub` (موزِّع `sad`) · `installers` · `lsp` · `pkg` · `profiler` · `repl` · `security-scanner` · `shared` · `wasm` |
| `tests/behavior/` (٦ حِزَم) | `P0_smoke` · `sections` · `rules_matrix` · `grammar_gaps` · `null_safety` · `_regression` |

> ⚠️ `rules_matrix` **تحت `tests/behavior/`** لا تحت `tests/` مباشرةً — ولهذا يكتب CI
> `--dir rules_matrix` بعد أن يقرأ `tests_dir: tests/behavior` من `config.yaml`.
> ولا وجود لمجلّد `tests/comprehensive`.

## ملفّات تُقرأ أولًا
| الملف | لماذا |
|------|------|
| `shared/lexer/include/token.h` | أنواع الرموز و`Position` |
| `language-truth/keywords.yaml` | معجم اللغة كلُّه: المحجوزُ والعواملُ اللفظيّة والسياقيُّ والأنواعُ المضمنة — ومنه يُولَّد المعجم |
| `shared/lexer/src/lexer_keywords.cpp` | تسجيل الكلمات المحجوزة (المولَّد منها) |
| `shared/types/include/value.h` | نوع القيم في وقت التشغيل |
| `shared/parser/include/parser_core.h` | واجهة المحلل (كل دوال `parse*`) |
| `interpreter/include/core/interpreter_core.h` | نقطة دخول المفسّر |
| `compiler/include/frontend/sir_types.h` | تعليمات/أنواع SIR |
| `language-truth/README.md` | مصدر الحقيقة |
| `tests/config.yaml` | مسارا الثنائيَّين اللذان يقيس بهما الـrunner |

---
**اقرأ بعده:** [أوّل مساهمة](first-contribution.md).
