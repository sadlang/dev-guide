# نظام الذاكرة (ذاكرة ص الذكية)

> **ماذا ستتعلّم:** كيف تُدير لغة ص الذاكرة عبر نظامٍ **مزدوج** — جامع قمامة (GC)
> سهلٌ للتطوير، وملكيّةٌ صارمة بصفر تكلفة للإنتاج — وكيف يُختار الوضع، وما الإعدادات
> المسبقة، وكيف يصل العلَم من سطر الأوامر إلى سلوك الذاكرة.

> 📎 المصدر: [`shared/memory_policy/include/memory/policy/gc_mode.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/include/memory/policy/gc_mode.h) · [`memory_mode_flag.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/include/memory/policy/memory_mode_flag.h) · [`memory_mode_flag.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/src/memory_mode_flag.cpp)

## الفكرة الجوهريّة: ذاكرةٌ مزدوجة

أغلب اللغات تختار مرّةً واحدة: إمّا GC (سهلٌ، لكن بتكلفة وقت تشغيل) أو ملكيّة يدويّة
(سريعٌ، لكن منحنى تعلّم حادّ). لغة ص تَجمع الطريقين في **وضعين قابلين للتبديل**، فالكود
نفسه يُجرَّب بـGC ثم يُشحَن بملكيّة صارمة:

```mermaid
flowchart TB
  CODE["كود .ص نفسه"]
  CODE --> DEV["وضع التطوير (--جامع)<br/>GC تلقائيّ · بلا تفكير في الملكيّة<br/>مثاليّ لـREPL والتجريب"]
  CODE --> PROD["وضع الإنتاج (--إنتاج)<br/>ملكيّة صارمة كـRust · صفر overhead<br/>فحص الاستعارة وقت الترجمة"]
  DEV -. "المترجم يقترح تحويلات للملكيّة" .-> PROD
```

> 💡 الميزة الفريدة: المترجم **يُحلِّل كود وضع التطوير ويقترح تحويلات تلقائيّة للملكيّة**
> (`enableOwnershipSuggestions`)، فينقلك من التجريب السريع إلى الإنتاج الصارم تدريجيًّا.

## ثلاثة تعدادات تَحكم كل شيء

السلوك كلّه ينضبط بثلاثة محاور مستقلّة (في [`gc_mode.h`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/include/memory/policy/gc_mode.h)):

```mermaid
flowchart LR
  subgraph MODE["MemoryMode — الوضع الرئيسيّ"]
    M1["Development"]:::a
    M2["Production"]:::a
    M3["Hybrid ⚠️ مهجور → GCOnly"]:::dep
    M4["Auto — اكتشاف بالسياق"]:::a
  end
  subgraph GC["GCStrategy — استراتيجيّة الجمع"]
    G1["None — بلا GC (إنتاج)"]:::b
    G2["ReferenceCounting — عدّ مراجع"]:::b
    G3["AtomicReferenceCounting — ذرّيّ (خيوط)"]:::b
    G4["Tracing — Mark & Sweep"]:::b
    G5["Incremental — تدريجيّ"]:::b
  end
  subgraph OWN["OwnershipMode — صرامة الملكيّة"]
    O1["Disabled — GC يدير كلّ شيء"]:::c
    O2["Warnings — تحذيرات للتعلّم"]:::c
    O3["Strict — أخطاء ترجمة"]:::c
    O4["UltraStrict — كـRust"]:::c
  end
  classDef a fill:#0b728522,stroke:#0b7285;
  classDef b fill:#2b8a3e22,stroke:#2b8a3e;
  classDef c fill:#e8590c22,stroke:#e8590c;
  classDef dep fill:#86868622,stroke:#868686,stroke-dasharray:4;
```

| المحور | التعداد | القيم |
|--------|---------|-------|
| الوضع | `MemoryMode` | `Development` · `Production` · `Hybrid` (مهجور) · `Auto` |
| الجمع | `GCStrategy` | `None` · `ReferenceCounting` · `AtomicReferenceCounting` · `Tracing` · `Incremental` |
| الملكيّة | `OwnershipMode` | `Disabled` · `Warnings` · `Strict` · `UltraStrict` |

> ⚠️ **`Hybrid` مهجور:** يُعامَل كـ`GCOnly` عند مصادفته. لا تُصمِّم على أساسه.

## الإعدادات المجمَّعة: `MemoryModeSettings`

البنية `MemoryModeSettings` تربط المحاور الثلاثة مع خياراتٍ إضافيّة (`enableCycleDetection`،
`gcMemoryLimitMB = 256`، `teacherMode`، …)، وتُقدَّم عبر **إعداداتٍ مسبقة** جاهزة:

| الإعداد المسبق | `mode` | `gcStrategy` | `ownershipMode` | اقتراحات | كشف دورات | مُعلِّم |
|----------------|--------|--------------|-----------------|:--------:|:---------:|:------:|
| `gcDefaults()` (`--جامع`) | Development | **Tracing** | Disabled | ✗ | ✓ | ✗ |
| `developmentDefaults()` | Development | ReferenceCounting | Warnings | ✓ | ✓ | ✓ |
| `productionDefaults()` (`--إنتاج`) | Production | **None** | **UltraStrict** | ✗ | ✗ | ✗ |
| `learningDefaults()` (`--تعلم`) | Development | ReferenceCounting | Warnings | ✓ | ✓ | ✓ |
| `kernelDefaults()` (`--حرّ`) | Production | None | UltraStrict | ✗ | ✗ | حدّ=0 |

> 📌 **النواة (`no_std`):** عند `#![بلا_مكتبة_قياسية]` يُفرَض `kernelDefaults` — لا GC إطلاقًا
> (`gcMemoryLimitMB = 0`)، ملكيّة `UltraStrict`، بلا اقتراحات ولا كشف دورات. ملكيّةٌ صرفة
> كما يليق ببرمجة الأنظمة.

## من العلَم إلى السلوك: `MemoryModeFlag`

[`MemoryModeFlag::parse()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/include/memory/policy/memory_mode_flag.h) يقرأ `argv` ويبني `MemoryModeSettings`.
الأعلام مسجَّلة في `flagHandlers_` ([`initializeFlags()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/src/memory_mode_flag.cpp#L54))،
وهي **مبنيّةٌ كلُّها من مصدر الحقيقة** ([`cli_flags.yaml`](https://github.com/sadlang/s-programming-language/blob/dev/language-truth/cli_flags.yaml)،
عائلة `memory`) لا مكتوبةً يدويًّا: التسمية تأتي من الجدول، ولا يبقى في C++ إلّا السلوك
(`switch` على `FlagAction`).

> ⚠️ **اسمٌ عربيٌّ قانونيٌّ وحيدٌ لكلّ مفهوم — لا مرادفات ولا اختصارات ولا توافقَ خلفيّ.**
> أُلغي 18 مرادفًا إنجليزيًّا/مختصرًا (`--gc` · `--no-std` · `--freestanding` · `--kernel` ·
> `--production`/`-p` · `--learn`/`-l` · `--auto`/`-a` · …)؛ يضبط المُهيِّئ
> `shortName = ""` و`longNameEnglish = longNameArabic`. فإن قرأت في وثيقةٍ أقدم علَمًا
> لاتينيًّا لسياسة الذاكرة، فهو **لم يعد يُقبَل**.

```mermaid
flowchart TD
  ARGV["argv[] / متغيّرات البيئة / ملف التهيئة"] --> PARSE["MemoryModeFlag::parse()"]
  PARSE --> H{"تصنيف العلَم"}
  H -->|"--إنتاج"| PROD["productionDefaults"]
  H -->|"--جامع"| GCD["gcDefaults"]
  H -->|"--تعلم"| LRN["learningDefaults"]
  H -->|"--حرّ"| KRN["kernelDefaults + noStdRequested"]
  H -->|"--تلقائي"| AUTO["اكتشاف بالسياق"]
  H -->|"--ملكية= · --جامع=استراتيجية · --حد-الذاكرة="| TUNE["ضبطٌ دقيقٌ فوق الإعداد المسبق"]
  H -->|"علَمٌ مُزال (--dev · --hybrid · --mixed …)"| REJ["فشلُ تحليلٍ صريح<br/>(لا تحويلَ صامت)"]
  PROD & GCD & LRN & KRN & AUTO & TUNE --> OUT["MemoryModeSettings ← FlagParseResult"]
```

**عائلة `memory` كاملةً على `dev`** (عشرةُ أعلام — لا غيرها):

| العلَم | النوع | الأثر (`sets`) |
|--------|-------|-----------------|
| `--إنتاج` | راية | `productionDefaults` — ملكيّة صارمة، بلا جامع |
| `--جامع[=استراتيجية]` | قيمة اختياريّة | `gcDefaults`؛ ومع قيمةٍ يضبط `gcStrategy` |
| `--تعلم` | راية | `learningDefaults` — جامع + تحذيرات + رسائل تعليميّة |
| `--حرّ` | راية | `kernelDefaults + noStdRequested` — ملكيّة صرفة بلا مكتبة قياسيّة |
| `--تلقائي` | راية | `MemoryMode::Auto` — اكتشافٌ بالسياق |
| `--ملكية=` | قيمة | `ownershipMode` (`off\|warnings\|strict\|ultra`) |
| `--حد-الذاكرة=` | قيمة | `gcMemoryLimitMB` — حدّ ذاكرة الجامع بالميغابايت |
| `--اقتراحات` | راية | `enableOwnershipSuggestions` |
| `--كشف-دورات` | راية | `enableCycleDetection` |
| `--تصحيح-الذاكرة` | راية | `DebugMemory` |

> 🛑 **الأعلام المُزالة تُرفَض، لا تُترجَم.** `--dev` · `--development` · `-d` · `--تطوير` ·
> `--hybrid` · `--mixed` · `--مختلط` كلُّها في جدول `deprecatedFlags`
> ([`memory_mode_flag.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/src/memory_mode_flag.cpp#L174))،
> لكنّ الجدول **لا يُحوِّلها**: يضبط `result.success = false` ويُصدِر «أُزيل نهائيًّا في
> Phase E-3، استخدم `--gc` بديلًا». الإحلالُ المذكور في الرسالة إرشادٌ للقارئ، لا
> تحويلٌ يجريه المُحلِّل — والبديلُ القانونيُّ اليومَ `--جامع`.

## ترتيب الأولويّة في حسم الإعداد

الإعداد النهائيّ يُحسَم بأولويّةٍ تصاعديّة (الأخصّ يَغلب):

```mermaid
flowchart LR
  D["الافتراضيّ (Auto)"] --> E["ملف التهيئة<br/>readConfigFile()"]
  E --> F["متغيّرات البيئة<br/>applyEnvironmentSettings()"]
  F --> G["سمة الملف #![…]"]
  G --> H["علَم سطر الأوامر<br/>(الأعلى أولويّة)"]
```

## أين يَظهر هذا في خطّ الأنابيب؟

- **المفسّر** (وضع GC الافتراضيّ): القيم الكائنيّة تُحمَل عبر `shared_ptr<ObjectInstance>`
  ([عدّ مراجع](#) ضمنيّ) — انظر [نظام الأنواع](types.md).
- **المترجم** (وضع الإنتاج): يولّد تخصيص/تحرير الذاكرة مباشرةً وفق الملكيّة عبر
  [`memory_codegen`](https://github.com/sadlang/s-programming-language/blob/dev/compiler/include/backend/llvm/builders/memory/memory_codegen.h) — انظر [توليد LLVM](../backend/llvm.md).
- **`no_std`**: المخصِّصات الحرّة [`sad_allocator.h`](https://github.com/sadlang/s-programming-language/blob/dev/runtime/freestanding/sad_allocator.h) و[`sad_bump_allocator.h`](https://github.com/sadlang/s-programming-language/blob/dev/runtime/freestanding/sad_bump_allocator.h).

> 🧭 القاعدة الذهبيّة: **الوضع سياسة، لا بنية**. الكود لا يتغيّر بين التطوير والإنتاج؛
> يتغيّر `MemoryModeSettings` فقط، فينتقل البرنامج من سهولة الـGC إلى صرامة الملكيّة دون
> إعادة كتابة.

---
**اقرأ بعده:** [نظام الأنواع (فاحص الأنواع)](types.md).
