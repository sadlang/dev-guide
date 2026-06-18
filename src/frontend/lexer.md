# المحلل المعجمي (Lexer)

> **ماذا ستتعلّم:** كيف يحوّل `LexerCore` نصّ `.ص` (UTF-8) إلى تيار `Token`، بتفصيل
> دقيق من الكود الفعليّ — بما فيه المعالجة الذكيّة للمحارف العربية متعدّدة البايتات.

> 📎 المصدر: [`shared/lexer/src/lexer_core.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp) · [`token.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/include/token.h) · [`lexer_keywords.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_keywords.cpp)

## البناء والنظر المسبق
`LexerCore(source)` يحتفظ بالمصدر ومؤشّر `current_` وموقع `Position`. الأدوات الأساسيّة:
- [`peek()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L102) — المحرف الحاليّ دون استهلاك.
- [`peekNext(offset)`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L132) — نظر مسبق.
- [`advance()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L160) — يستهلك ويتقدّم (يحدّث السطر/العمود).
- [`skipWhitespace()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L248) — يتخطّى الفراغات.

`Position` يبدأ من 1 (سطر/عمود) و`offset` من 0.

## موزِّع `nextToken()` — ترتيب الإرسال
الدالة المحوريّة [`nextToken()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1559) تتبع ترتيبًا **حسّاسًا** (الترتيب يمنع لبس المحارف العربية):

```mermaid
flowchart TD
  N["nextToken()"] --> WS["حلقة: skipWhitespace + التعليقات (# #* ## #**)"]
  WS --> EOF{"نهاية الملف؟"}
  EOF -- نعم --> E["END_OF_FILE"]
  EOF -- لا --> D{"تصنيف المحرف"}
  D -->|رقم عربيّ/إنجليزيّ| NUM["scanNumber()"]
  D -->|'r\"' أو 'ح\"'| RAW["scanRawString()"]
  D -->|'f\"' أو 'م\"' أو 'ص\"'| FS["scanFString()"]
  D -->|'\"'| STR["scanString()"]
  D -->|'×' (0xC3 0x97)| MUL["OP_MULTIPLY"]
  D -->|'،' '؛' '؟' (0xD8 ..)| ARB["ARABIC_COMMA / SEMICOLON / QUESTION"]
  D -->|حرف/‎_‎/عربيّ| ID["scanIdentifier()"]
  D -->|عامل| OP["scanOperator()"]
```

### ⭐ المعالجة الدقيقة لـUTF-8 (نقطة متقدّمة)
المحارف العربية متعدّدة البايتات **تُفحَص قبل `scanIdentifier`** وإلّا ابتلعها كجزء من مُعرّف:

| المحرف | UTF-8 | الرمز الناتج | الموقع |
|--------|-------|--------------|--------|
| رقم عربيّ ٠–٩ | `0xD9` + `0xA0..0xA9` | عدد → `scanNumber` | [L1646](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1646) |
| `ح"` (نصّ خام) | `0xD8 0xAD` + `"` | `STRING_RAW` | [L1675](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1675) |
| `م"` / `ص"` (نصّ منسَّق) | `0xD9 0x85` / `0xD8 0xB5` + `"` | `STRING_FSTRING` | [L1694](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1694) |
| `×` ضرب | `0xC3 0x97` | `OP_MULTIPLY` | [L1726](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1726) |
| `،` فاصلة | `0xD8 0x8C` | `ARABIC_COMMA` | [L1743](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1746) |
| `؛` منقوطة | `0xD8 0x9B` | `ARABIC_SEMICOLON` | [L1753](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1753) |
| `؟` استفهام | `0xD8 0x9F` | `QUESTION` (و`؟.`→`QUESTION_DOT`) | [L1760](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1760) |

> 💡 لهذا تعمل `س، ص` و`أ ؟ ب : ج` و`٣ × ٤` كما لو كُتبت باللاتينيّة — المعجمي يطبّع المحارف العربية إلى رموز قياسيّة.

## الماسحات (Scanners)
| الدالة | الموقع | يمسح |
|--------|--------|------|
| [`scanNumber`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L323) | L323 | صحيح/عشريّ + `0x`/`0b`/`0o`؛ يترك `..` لماسح العوامل (المدى) |
| [`scanString`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L754) | L754 | `"..."` مع هروب `\n \t \\ \" \r \b \f \v \0 \u \U \x` |
| [`scanRawString`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L998) | L998 | `r"..."`/`ح"..."` بلا معالجة هروب |
| [`scanFString`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1054) | L1054 | `f"...{تعبير}..."` |
| [`scanDocComment`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1167) | L1167 | `##` / `#** **#` (يُرفَق بأوّل تصريح) |
| [`scanIdentifier`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1250) | L1250 | مُعرّف UTF-8 (يتوقّف قبل `،`/`؛`) |
| [`scanOperator`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_core.cpp#L1347) | L1347 | العوامل (switch على `+ - * / % = < > ! . ^ | & ~`) |

## التعليقات
حلقة التخطّي في بداية `nextToken` تعالج: `#` سطر · `#* … *#` كتلة · `##` توثيق سطر ·
`#** … **#` توثيق كتلة (التعليق غير المغلق يرمي خطأً). تعليقات `##` تُلتقَط وتُرفَق لاحقًا
بأوّل تصريح ([انظر تهيئة المحلل النحوي](parser.md)).

## الكلمات والرموز
- **محجوزة (40):** مسجّلة في [`lexer_keywords.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/lexer/src/lexer_keywords.cpp) (`KeywordTable::initialize()`)، مصدرها `language-truth/keywords.yaml`.
- **سياقيّة:** لها `KEYWORD_*` في `token.h` لكنها **لا تُسجَّل** كمحجوزة؛ يميّزها المحلل النحوي بالسياق.
- **أنواع مدمجة كمُعرّفات:** `رقم`/`نص`/… ليست محجوزة.

## إضافة كلمة مفتاحيّة (مختصر)
1. أضف `KEYWORD_FOO` إلى `token.h`. 2. محجوزة: سجّلها في `keywords.yaml` ثم أعد توليد
`keywords_generated`. سياقيّة: لا تسجّلها، واستخدم التحقّق المزدوج في المحلل النحوي.
3. أضف القاعدة + عقدة AST + الزوّار + codegen + اختبار. → [التشابك](../architecture/interconnected.md).

---
**اقرأ بعده:** [المحلل النحوي](parser.md).
