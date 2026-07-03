# دراسة حالة: الاستيعابات (من `أنتج` إلى SIR)

مثالٌ متكامل على تمرير ميزة لغويّة عبر خطّ الأنابيب: كيف تُحلَّل الاستيعابات (قوائم/
مجموعات/قواميس) بترتيب `أنتج` العربيّ، وتُبنى في AST، وتُنفَّذ في المحرّكين. المرجع
اللغويّ للمستخدم في [sadlang-docs](https://github.com/sadlang/sadlang-docs)؛ هذه
الصفحة للمساهم في **التنفيذ**.

الصيغة: `[لكل <متغيّر> في <مصدر> [إذا <شرط>] أنتج <ناتج>]` (والمعقوفة `{}` للمجموعة/
القاموس). أُقرّت في RFC 25 (م1ب).

> **المبدأ الأهمّ:** التغيير في **المحلّل فقط**. عقد AST لم تتغيّر (نفس الحقول)، فلم
> يُمَسّ المفسّر ولا المترجم في *بناء العقدة* — فقط **ترتيب القراءة** انقلب. هذا يقلّل
> سطح التغيير جذريًّا ويحافظ على تكافؤ المحرّكين.

---

## 1) المحلّل: كشف مبكّر + تمييز

الاستيعاب يُكتشَف **مبكّرًا** عبر `لكل` (KEYWORD_FOR) في أوّل المحتوى، قبل تحليل أيّ
تعبير — فلا لبس مع مصفوفة/خريطة عاديّة:

- القائمة:
  [`ParserCore::parseArrayLiteral`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/statements/parser_advanced.cpp)
  — إن كان أوّل رمز `لكل`: `في` → مصدر → `[إذا شرط]` → `أنتج` → ناتج → `]`.
- المجموعة/القاموس:
  [`ParserCore::parseMapLiteral`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/statements/parser_advanced.cpp)
  — بعد `أنتج` يُحلَّل الناتج الأوّل بـ`parseTernary` (لتجنّب التهام `:`)، ثمّ:
  **وجود `:` (أو `=`) ⇒ قاموس** (نُحلّل القيمة)، **غيابها ⇒ مجموعة**.

`أنتج` = `KEYWORD_YIELD` **السياقيّة الموجودة أصلًا** (تُستعمَل أيضًا للتوليد)، فلا
تعديل على [`keywords.yaml`](https://github.com/sadlang/s-programming-language/blob/dev/language-truth/keywords.yaml).
شرط القبول: `match(KEYWORD_YIELD) || matchContextual(KEYWORD_YIELD)` (في الكود حارسٌ
منفيّ: `if (!match(...) && !matchContextual(...)) error`).

> **فخّ:** الترتيب البايثونيّ القديم (`[تعبير لكل …]`) لم يعد يُبنى كاستيعاب — يُحلَّل
> كمصفوفة عاديّة ثمّ يتعثّر عند `لكل`. حُذفت دالّتا `parseListComprehension`/
> `parseDictComprehension` القديمتان من **مسار المحلّل الحيّ** (`parser_helpers.cpp`).
> (تبقى نسخة بالترتيب القديم في `shared/parser/src/specs/flow/parser_comprehension.cpp`
> لكنّها نموذج ميت **غير مُترجَم** — لا إحالة إليه في CMake؛ يُنظَّف في طور لاحق.)

---

## 2) عقد AST (لم تتغيّر)

في [`shared/ast/include/expressions.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/ast/include/expressions.h)
(لا `comprehension_nodes.h` الميت):

| العقدة | الحقول |
|---|---|
| `ListComprehensionExpr` | `element`، `variable`، `iterable`، `condition` |
| `SetComprehensionExpr` | `expression`، `variable`، `iterable`، `condition` |
| `DictComprehensionExpr` | `key`، `value`، `variable`، `iterable`، `condition` |

القاموس بمتغيّر حلقة **مفرد** (أُسقطت الصيغة الثنائيّة `م، ق` القديمة — كانت في دالّة
ميتة بلا مستهلك).

---

## 3) الواجهة الخلفيّة: التوليد في SIR

بانيات الاستيعاب في `compiler/src/frontend/builders/`:

- **القائمة والقاموس** —
  [`expression_comprehensions.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/compiler/src/frontend/builders/expression_comprehensions.cpp):
  `buildExprListComp` يستعمل أوكواد المصفوفة المُلوَّنة في الخلفيّة
  (`ARRAY_NEW`/`ARRAY_LEN`/`ARRAY_GET`/`ARRAY_APPEND`)، و`buildExprDictComp` يستعمل
  `__sad_map_create` + `__sad_map_set_typed` (نفس مسار الخريطة الحرفيّة). هذا هو
  الإصلاح التاريخيّ لـISSUE-016/017 (بدل نداءات رموز وقت تشغيل غير معرَّفة).
- **المجموعة** —
  [`expression_comp2.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/compiler/src/frontend/builders/expression_comp2.cpp):
  `buildExprSetComp`. المجموعة = **مصفوفة بعناصر فريدة** (كالمفسّر). يستعمل نفس أوكواد
  المصفوفة **زائد حلقة مسح داخليّة لإزالة التكرار**: يبني قيمة الناتج، يمسح مصفوفة
  النتيجة، ويضيف عبر `ARRAY_APPEND` **فقط إن غابت القيمة**. إزالة التكرار على **قيمة
  الناتج** (لا متغيّر الحلقة) — مطابقةً للمفسّر.

> **لماذا بانٍ منفصل للمجموعة؟** إزالة التكرار تُدخِل حلقة مسح داخليّة متداخلة
> (كتل `scan_cond`/`scan_body`/`scan_found`/`scan_next`/`scan_done`/`append`) تضاعف
> حجم البانِي، فلا تتقاسم بنية List/Dict المستقيمة؛ ويشارك الملفّ `buildExprGenerator`.

نقاط تنفيذ دقيقة في بانِي المجموعة:

- علَم «موجود» وعدّاد المسح الداخليّ يُخصَّصان بـ`ALLOC` **مرّة في كتلة الدخول** (قبل
  الحلقة الخارجيّة) — لا داخل الجسم — تفاديًا لتسريب مكدس (alloca متكرّر لكلّ عنصر).
- هيمنة SSA محفوظة: `elemExprResult` يُعرَّف في كتلة القيمة التي تُهيمِن على عنقود
  المسح والإضافة؛ `curIdxReg` يُعرَّف في كتلة الشرط التي تُهيمِن على الجسم والزيادة.

> **حدّ معروف:** مقارنة إزالة التكرار (`EQ`) **عدديّة** (كبقيّة بنية الاستيعابات
> عدديّة النوع)، فالمجموعات الصحيحة الإزالة للأعداد؛ مجموعات النصوص/العشريّ تتباعد
> صامتًا حتى يُعمَّم النوع في الاستيعابات الثلاثة.

> **فخّ متبقٍّ:** `buildExprGenerator` في نفس الملفّ ما زال بالنهج المكسور (`CALL
> __sad_len`/`__sad_array_push` غير المعرَّفة) — سينهار الربط متى استُخدم مولِّد؛ خارج
> نطاق م1ب، يُتابَع بنفس نمط الإصلاح.

---

## 4) الاختبار (طبقتان)

- **سلوك (تكافؤ مزدوج)** — `tests/behavior/rules_matrix/60_advanced/gr.adv.{list,set,
  dict}_comprehension/`، مولَّدة بـ`_generators/gen_comprehension_tests.py` (يحاكي
  الدلالة في بايثون ⇒ `@expected` حتميّ). **حسّاس:** اختبارات المجموعة تستعمل خرائط
  **غير حقنيّة** (`س % 3`) + probe قيمة بالفهرسة — وإلّا فخريطة حقنيّة تجعل الطول
  مستقلًّا عن التحويل، فيمرّ محرّك يتجاهل `أنتج` أو يزيل التكرار على المصدر **زائفًا**.
- **وحدة (C++)** — [`tests/unit/parser/test_comprehensions_antaj.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/tests/unit/parser/test_comprehensions_antaj.cpp)
  (إطار `sad_test.h`): يتحقّق من عقد AST + تمييز قاموس/مجموعة + رفض الترتيب القديم +
  بنية `BinaryExpr` للناتج. مُسجَّل في CTest كـ`ComprehensionAntajTests` (وسم `Unit`)
  عبر [`cmake/tests.cmake`](https://github.com/sadlang/s-programming-language/blob/dev/cmake/tests.cmake).

---

## انظر أيضًا

- [المحلل النحوي (Parser)](parser.md) · [شجرة AST](ast.md) · [التمثيل الوسيط SIR](../backend/sir.md)
- [قواعد المحلل كمصدر موحّد](../sot/grammar-sot.md) — قواعد `gr.adv.*_comprehension` في `language-truth/grammar/`.
