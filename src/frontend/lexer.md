# المحلل المعجمي (Lexer)

> **ماذا ستتعلّم:** كيف يحوّل `LexerCore` نصّ `.ص` إلى تيار `Token`، وأين الكلمات المحجوزة.

## الدور
يقرأ المصدر (UTF-8) حرفًا حرفًا ويُنتج `Token`ات. يتعامل مع العربية والإنجليزية في
الأسماء والنصوص، ويتخطّى المسافات والتعليقات، ويجمّع تعليقات التوثيق `##`.

## الملفّات
| الملف | المحتوى |
|------|---------|
| `shared/lexer/include/token.h` | تعداد `TokenType` + `Token` + `Position` |
| `shared/lexer/src/lexer_core.cpp` | `LexerCore::nextToken()` / `tokenize()` |
| `shared/lexer/src/lexer_keywords.cpp` | `KeywordTable::initialize()` — تسجيل الكلمات المحجوزة |
| `shared/lexer/generated/keywords_generated.{h,cpp}` | **مُولَّد** من `keywords.yaml` |

## أنواع الرموز
- **كلمات محجوزة (40):** `دالة`، `ارجع`، `صنف`، `إذا`، `بينما`، `نهاية`، … مسجّلة في `lexer_keywords.cpp`.
- **كلمات سياقيّة:** مثل `سمة`، `نفّذ`، `ماكرو`، `أجّل` — لها `KEYWORD_*` في `token.h` لكنها **لا تُسجَّل** كمحجوزة؛ يميّزها المحلل النحوي بالسياق.
- **أنواع مدمجة كمُعرّفات:** `رقم`، `نص`، … ليست محجوزة (تصلح أسماء متغيّرات).
- طرفيّات: `IDENTIFIER`، `NUMBER_INTEGER/DOUBLE`، `STRING_LITERAL/RAW/FSTRING`، `LIFETIME`، `COMMENT/DOC_COMMENT`، عوامل ورموز.

## التهيئة والنظر المسبق
`ParserCore` يطلب رمزين مسبقًا (`current_`, `nextToken_`) لتمكين lookahead، متخطّيًا
`WHITESPACE/COMMENT/DOC_COMMENT/NEWLINE`. `Position` يبدأ من 1 (سطر/عمود) و`offset` من 0.

## التعليقات
`#` سطر · `#* … *#` كتلة · `##` أو `#** … **#` توثيق (يُرفَق بأوّل تصريح تالٍ).

## إضافة كلمة مفتاحيّة (الإجراء المختصر)
1. أضف `KEYWORD_FOO` إلى `token.h`.
2. **محجوزة:** اربطها في `keywords.yaml` ثم أعد توليد `keywords_generated`.
   **سياقيّة:** لا تسجّلها؛ استخدم التحقّق المزدوج في المحلل النحوي.
3. أضف القاعدة في المحلل النحوي + عقدة AST + الزوّار + codegen + اختبار.

> راجع [المحلل النحوي](parser.md) و[التشابك](../architecture/interconnected.md).

---
**اقرأ بعده:** [المحلل النحوي](parser.md).
