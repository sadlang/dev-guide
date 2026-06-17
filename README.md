<div dir="rtl">

# دليل مطوّري لغة ص — الأنظمة الداخلية

> **مرجع المطوّرين الذين يطوّرون لغة ص نفسها** (المفسّر، المترجم، الأنظمة الداخلية) —
> لا مَن يكتبون برامج *بها*. مبنيّ كـ[mdBook](https://rust-lang.github.io/mdBook/)،
> مستوحى من [`rustc-dev-guide`](https://rustc-dev-guide.rust-lang.org/) ومُصمَّم
> ليكون **أوضح تنظيمًا وأكثر تطوّرًا**: معماريّة طبقيّة صريحة + **مصدر حقيقة موحّد
> (data-driven)** يميّز لغة ص.

[![mdBook](https://img.shields.io/badge/built%20with-mdBook-navy)](https://rust-lang.github.io/mdBook/)
[![لغة ص](https://img.shields.io/badge/sadlang-internals-success)](https://github.com/sadlang/s-programming-language)
[![نشر](https://github.com/sadlang/dev-guide/actions/workflows/deploy.yml/badge.svg)](https://github.com/sadlang/dev-guide/actions/workflows/deploy.yml)

🌐 **النسخة المنشورة:** https://sadlang.github.io/dev-guide/ (تُبنى آليًّا من `main`).

## ما الذي يميّز هذا الدليل؟

| | rustc-dev-guide | دليل لغة ص |
|---|---|---|
| البنية | فصول مسطّحة | **أجزاء مُرقّمة** (بدء → معمارية → SoT → أمام → خلف → أنظمة → مساهمة) |
| القواعد النحويّة | نثر + كود المحلل | **مصدر موحّد YAML** (`language-truth/grammar/`) يُولِّد التوثيق والمخطّطات |
| بيانات اللغة | موزّعة في الكود | **`language-truth/` SoT** (كلمات/عوامل/أنواع/أخطاء/مضمنة) + codegen |
| المخطّطات | محدودة | **Mermaid** لكل خطّ أنابيب وكل تدفّق |
| المساهمة | فروع + PR | **worktrees معزولة + فرع `dev` محميّ + PR موقّع GPG** |

## البناء محليًّا

```bash
cargo install mdbook mdbook-mermaid
mdbook-mermaid install .      # يُضيف أصول mermaid
mdbook serve --open          # معاينة حيّة على http://localhost:3000
mdbook build                 # ينتج ./book
```

## البنية

```
dev-guide/
├── book.toml            ← إعداد mdBook
├── src/
│   ├── SUMMARY.md       ← الفهرس (شجرة الفصول)
│   ├── introduction.md
│   ├── getting-started/ · architecture/ · sot/ · frontend/ · backend/ · systems/ · contributing/
│   └── glossary.md
└── theme/rtl.css        ← دعم العربية (RTL)
```

## المصادر المرتبطة

- **المستودع الرئيسيّ:** [`sadlang/s-programming-language`](https://github.com/sadlang/s-programming-language)
- **مصدر الحقيقة:** `language-truth/` · **قواعد المحلل:** `language-truth/grammar/` + `docs/parser_rule/_generated/`
- **مهارة التطوير:** `.github/skills/sad-lang-dev/`

## المساهمة

اقرأ [دليل المساهمة](CONTRIBUTING.md). باختصار: فرع `agent/<مهمة>` في worktree من `dev` →
commit موقّع GPG → PR إلى `dev` (الدفع المباشر ممنوع).

## الرخصة

MIT — كالمشروع الأمّ.

</div>
