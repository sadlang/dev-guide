# المحلل النحوي (Parser)

> **ماذا ستتعلّم:** بنية المحلل النزوليّ التعاوديّ، نقطة الدخول، الموزِّعات، سلسلة
> أسبقيّة التعابير، وآليّة الكلمات السياقيّة — بتفصيل دقيق من الكود.

> 📎 المصدر: [`shared/parser/src/core/parser_main.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_main.cpp) · [`parser_expressions.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp) · [`parser_core.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/include/parser_core.h)

## البنية
`Sad::Parser::ParserCore` محلل **نزوليّ تعاوديّ** يحوّل تيار الرموز إلى AST. كل قاعدة ≈
دالة `parseXxx()`. الكود موزّع على `core/`، `statements/`، `declarations/`، `specs/`، `ui/`.
التهيئة ([`ParserCore::ParserCore`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_main.cpp#L42)) تجلب **رمزين مسبقًا** (`current_`, `nextToken_`)
وتتخطّى الفراغات/التعليقات وتجمّع تعليقات `##` المعلّقة.

## نقطة الدخول والموزِّعات
```mermaid
flowchart TD
  P["parseProgram() — L124"] -->|while !isAtEnd| D["parseDeclaration() — L364"]
  D -->|كلمة تصريح| DECL["دالة/صنف/متغيّر/تعداد/استيراد/…"]
  D -->|@| DIR["tryParseDirective() — L1479"]
  D -->|غير ذلك| S["parseStatement() — L1173"]
  S -->|كلمة جملة| CF["إذا/بينما/لكل/طابق/حاول/…"]
  S -->|افتراضي| ES["parseExpressionStmt() → parseExpression()"]
```

- [`parseProgram()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_main.cpp#L124) — يكرّر `parseDeclaration` حتى نهاية الملف، مع **حماية من الحلقة اللانهائيّة** (`MAX_STUCK_ITERATIONS=3`) وعدّ الدوال الرئيسيّة.
- [`parseDeclaration()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_main.cpp#L364) — موزّع التصريحات (~33 فرعًا): توجيهات `@`، مُزخرِفات، سمات `[[..]]`، استورد/من/صدّر/خارجي، دالة/مولد/async، قالب/فضاء، صنف/سمة/نفّذ/امتداد/ماكرو/نوع/عقد، متغير/ثابت، تصريح ببدء النوع/الصنف، اختبر/حالة/اعرض، تعداد/بنية، وأخيرًا `parseStatement`.
- [`parseStatement()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_main.cpp#L1173) — موزّع الجمل: إذا/بينما/لكل/حالة/طابق/ارجع/أنتج/باستخدام/أجّل/أطلق/اختر/توقف/استمر/`{`/حاول/ارمي، وافتراضيًّا جملة تعبير.

## سلسلة أسبقيّة التعابير
من الأدنى ربطًا (أعلى المستوى) إلى الأعلى — كل دالة تستدعي الأعلى أسبقيّةً ثم تحلّق على عاملها:

| المستوى | الدالة | العامل |
|---------|--------|--------|
| 1 | [`parsePipeline`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L51) | `\|>` |
| 2 | [`parseAssignment`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L103) | `= := += -= *= /= //= %=` |
| 3 | [`parseTernary`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L378) | `? :` |
| 4 | `parseNullCoalesce` | `??` |
| 5–10 | `parseLogicalOr/And` · `parseBitwiseOr/Xor/And` | `\|\| && \| ^ &` |
| 11–12 | `parseEquality` · `parseComparison` | `== != < <= > >= في` |
| 13 | [`parseRange`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L594) | `..` |
| 14–15 | `parseTerm` · `parseFactor` | `+ - << >>` · `* / // %` |
| 16 | [`parseUnary`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L675) | `! - ~ ++ -- &`(استعارة) |
| 17 | `parsePower` | `**` (يمينيّ) |
| 18 | [`parsePostfix`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L747) | `() . ?. [] ++ -- !()` |
| 19 | [`parsePrimary`](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L1116) | القيم الذريّة |

هذا الترتيب **يُعرّف أسبقيّة العوامل** — ومصدره `language-truth/operators.yaml`.

## ⭐ الكلمات السياقيّة (التحقّق المزدوج)
كثير من «الكلمات» (سمة/نفّذ/امتداد/ماكرو/حالة/أجّل/أطلق/اختر) **ليست محجوزة**؛ يتعرّف
عليها المحلل بنمطٍ مزدوج + نظر مسبق:

```cpp
// قاعدة سياقيّة: تُعامَل تصريحًا فقط إن تلاها مُعرّف (وإلا مُعرّف عاديّ)
if (match(TT::KEYWORD_TRAIT) ||
    (check(TT::IDENTIFIER) && peekNext().getType() == TT::IDENTIFIER
     && current_.getValue() == "سمة" && (advance(), true))) {
    return parseTraitDecl();
}
```

مثال على فضّ الغموض: `أجّل` تُعامَل جملةً إلّا إن تلاها `=`/`+=`/`.` (فتصير مُعرّفًا).
هذا يسمح باستعمال هذه الكلمات أسماءَ متغيّرات خارج سياقها.

## السكر النحوي (Desugaring)
يُحوِّل المحلل بعض الصياغة وقت التحليل:
- الأنبوب: `أ |> د` ← `د(أ)` · `أ |> د(ب)` ← `د(أ، ب)` ([parsePipeline L70](https://github.com/sadlang/s-programming-language/blob/dev/shared/parser/src/core/parser_expressions.cpp#L70)).
- الإسناد المركّب: `س += ص` ← `س = س + ص` (يعيد بناء طرف القراءة للحقول/الفهارس المتداخلة).
- القيمة المطلقة: `|تعبير|` ← `abs(تعبير)`.

## التعافي من الأخطاء
عند الخطأ، يُستدعى `synchronize()` للقفز إلى نقطة مزامنة (بينما/حاول/امسك/صنف/…)
المُسجَّلة في `recoverySystem_`، وتُجمَّع التشخيصات في `ErrorManager`. → [نظام الأخطاء](../systems/errors.md).

## التوثيق الكامل للقواعد
قواعد المحلل **موثّقة كمصدر موحّد** (BNF + مخطّطات + مسار حتى AST) — راجع
[قواعد المحلل SoT](../sot/grammar-sot.md) و`docs/parser_rule/_generated/` في المستودع الرئيسيّ.

---
**اقرأ بعده:** [شجرة AST](ast.md).
