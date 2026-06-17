# ‏`language-truth/` — كتالوج اللغة

> **ماذا ستتعلّم:** بنية مجلد مصدر الحقيقة، وملفّاته، ومخطّطاته، وكيف تعدّله بأمان.

## البنية
```
language-truth/
├── keywords.yaml          ← الكلمات المفتاحيّة (محجوزة + سياقيّة) + tokenType + KW-RES-NNN
├── operators.yaml         ← العوامل: الرمز، الأسبقية، الترابط، op.<name>
├── types.yaml             ← الأنواع المدمجة
├── directives.yaml        ← توجيهات @ (حجم/ذري/غير_آمن/…)
├── *_constructs.yaml      ← تراكيب اللغة (oop/expr/grammar)
├── builtins/              ← الدوال المضمنة لكل نطاق (+ _index.yaml)
├── errors/                ← رموز ورسائل الأخطاء (مصدر V5)
├── grammar/               ← ⭐ قواعد الإنتاج النحويّة (SoT) — انظر فصلها
├── _schemas/              ← مخطّطات JSON للتحقّق من كل ملف
└── _meta/ · _notation/ · learning/ · stdlib/ · tests/
```

## أمثلة على الصيغة
**كلمة مفتاحيّة** (`keywords.yaml`):
```yaml
- { id: "KW-RES-012", subcategory: "control_flow", since: "1.0.0",
    word: "إذا", tokenType: KEYWORD_IF, english: if,
    aliases: ["اذا"], roles: [block_opener] }
```

**عامل** (`operators.yaml`) — يحمل الأسبقية والترابط (مصدر سلسلة المحلل):
```yaml
- { id: op.assign, symbol: "=", name_ar: "إسناد", category: assignment,
    arity: binary, precedence: 15, associativity: right, since: "1.0.0", status: stable }
```

## التحقّق بالمخطّطات
كل ملف يُتحقَّق ضدّ مخطّط في `_schemas/` (مثل `keywords.schema.json`،
`grammar_production.schema.json`). هذا يمنع الانجراف ويضمن صحّة البنية آليًّا.

## تعديله بأمان (الإجراء)
1. عدّل **YAML المصدر** فقط (لا `generated/`).
2. أعد التوليد بالمولّد المعنيّ (→ [توليد الكود](codegen.md)).
3. تأكّد من تطابق YAML + المُولَّد، وضمّنهما في **نفس الـcommit**.
4. حدّث الطبقات المستهلِكة (parser/visitors/codegen) واكتب اختبارًا.

> **ثوابت مُولَّدة لا سلاسل حرفيّة:** سجّل الدوال بـ`Bn::<Group>::<CPP_ID>`، وطرق
> الأنواع بـ`TM::<Group>::<NAME>`، وأطلِق الأخطاء بـ`ErrorCode::<NAME>`. يُمنع نصّ خطأ حرّ.

---
**اقرأ بعده:** [توليد الكود](codegen.md).
