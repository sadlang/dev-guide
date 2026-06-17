# خريطة المستودع

> **ماذا ستتعلّم:** أين يعيش كل شيء في `sadlang/s-programming-language`.

```
s-programming-language/
├── shared/                 ← النواة المشتركة
│   ├── lexer/              ← المحلل المعجمي + Token + Position
│   ├── parser/             ← المحلل النحوي (recursive descent)
│   ├── ast/                ← عقد شجرة AST + ASTVisitor
│   ├── types/              ← Value (نوع القيم الموحّد) + SadType
│   └── errors/             ← نظام الأخطاء + رموزها
├── interpreter/            ← المفسّر الشجريّ (InterpreterCore + visitors + builtins)
├── compiler/               ← المترجم: AST → SIR → LLVM IR → تنفيذيّ
│   ├── src/frontend/       ← SIRBuilder + sir_types.h (opcodes الملكية)
│   └── src/backend/llvm/   ← LLVMCodeGen + builders
├── vm/                     ← الآلة الافتراضية (بايت كود مرتبط بالمفسّر)
├── stdlib/                 ← المكتبة القياسية (core/io/math/string/network/graphics)
├── runtime/                ← ABI/FFI المستقلّ + ربط VM
├── tools/                  ← sadinfo · lsp · formatter · pkg · repl · compiler(sadc CLI)
├── language-truth/         ← ⭐ مصدر الحقيقة الموحّد (YAML)
│   ├── keywords.yaml · operators.yaml · types.yaml · directives.yaml
│   ├── builtins/ · errors/ · grammar/   ← قواعد الإنتاج (SoT)
│   └── _schemas/                        ← مخطّطات JSON للتحقّق
├── scripts/codegen/        ← gen_*.py (تقرأ YAML وتُنتج C++/توثيق)
├── docs/                   ← توثيق (incl. parser_rule/_generated المُولَّد)
├── tests/                  ← اختبارات .ص + rules_matrix + comprehensive
├── _bmad-output/           ← نظام الحوكمة (سياسات/ستوريات/قرارات)
└── .github/skills/         ← مهارات الوكلاء (sad-lang-dev …)
```

## ملفّات تُقرأ أولًا
| الملف | لماذا |
|------|------|
| `shared/lexer/include/token.h` | أنواع الرموز و`Position` |
| `shared/lexer/src/lexer_keywords.cpp` | تسجيل الكلمات المحجوزة (40) |
| `shared/types/include/value.h` | نوع القيم في وقت التشغيل |
| `shared/parser/include/parser_core.h` | واجهة المحلل (كل دوال `parse*`) |
| `interpreter/include/core/interpreter_core.h` | نقطة دخول المفسّر |
| `compiler/include/frontend/sir_types.h` | تعليمات/أنواع SIR |
| `language-truth/README.md` | مصدر الحقيقة |

---
**اقرأ بعده:** [نظرة عامّة على الطبقات](../architecture/overview.md).
