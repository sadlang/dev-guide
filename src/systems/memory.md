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
  CODE --> DEV["وضع التطوير (--gc)<br/>GC تلقائيّ · بلا تفكير في الملكيّة<br/>مثاليّ لـREPL والتجريب"]
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
| `gcDefaults()` (`--gc`) | Development | **Tracing** | Disabled | ✗ | ✓ | ✗ |
| `developmentDefaults()` | Development | ReferenceCounting | Warnings | ✓ | ✓ | ✓ |
| `productionDefaults()` (`--إنتاج`) | Production | **None** | **UltraStrict** | ✗ | ✗ | ✗ |
| `learningDefaults()` (`--تعلم`) | Development | ReferenceCounting | Warnings | ✓ | ✓ | ✓ |
| `kernelDefaults()` (`--نواة`) | Production | None | UltraStrict | ✗ | ✗ | حدّ=0 |

> 📌 **النواة (`no_std`):** عند `#![بلا_مكتبة_قياسية]` يُفرَض `kernelDefaults` — لا GC إطلاقًا
> (`gcMemoryLimitMB = 0`)، ملكيّة `UltraStrict`، بلا اقتراحات ولا كشف دورات. ملكيّةٌ صرفة
> كما يليق ببرمجة الأنظمة.

## من العلَم إلى السلوك: `MemoryModeFlag`

[`MemoryModeFlag::parse()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/include/memory/policy/memory_mode_flag.h) يقرأ `argv` ويبني `MemoryModeSettings`.
الأعلام مسجَّلة في `flagHandlers_` ([`initializeFlags()`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/src/memory_mode_flag.cpp#L142))، ولكلّ علَمٍ عربيٍّ مرادفاتٌ إنجليزيّة ومختصرة:

```mermaid
flowchart TD
  ARGV["argv[] / متغيّرات البيئة / ملف التهيئة"] --> PARSE["MemoryModeFlag::parse()"]
  PARSE --> H{"تصنيف العلَم"}
  H -->|"--إنتاج / --production / -p"| PROD["productionDefaults"]
  H -->|"--gc / --dev*(مهجور)"| GCD["gcDefaults"]
  H -->|"--تعلم / --learn / -l"| LRN["learningDefaults"]
  H -->|"--نواة / --no-std / --kernel"| KRN["kernelDefaults"]
  H -->|"--تلقائي / --auto / -a"| AUTO["اكتشاف بالسياق"]
  H -->|"--ملكية= / --gc-strategy= / --حد_ذاكرة="| TUNE["ضبطٌ دقيقٌ فوق الإعداد المسبق"]
  PROD & GCD & LRN & KRN & AUTO & TUNE --> OUT["MemoryModeSettings ← FlagParseResult"]
```

**جدول الأعلام الرئيسيّة** (عربيّ ← مرادفات):

| العربيّ | المرادفات | الأثر |
|---------|-----------|-------|
| `--إنتاج` | `--production` · `--prod` · `--release` · `-p` | ملكيّة صارمة، بلا GC |
| `--gc` | `--dev`*، `--development`*، `--تطوير`*، `-d`* | GC (يحلّ محلّ `--dev` المهجور) |
| `--تعلم` | `--learn` · `--learning` · `-l` | GC + تحذيرات + رسائل تعليميّة |
| `--نواة` | `--no-std` · `--kernel` · `--freestanding` · `--بلا-مكتبة-قياسية` | ملكيّة صرفة `no_std` |
| `--ملكية=` | `--ownership=` | يضبط `OwnershipMode` يدويًّا |
| `--gc-strategy=` | — | يختار `GCStrategy` |
| `--حد_ذاكرة=` | `--gc-memory-limit=` | حدّ ذاكرة الـGC بالميغابايت |

> 🔁 `--dev`/`--تطوير`/`--mixed` تُحوَّل جميعها إلى `--gc` (تنبيهُ إهجار) — انظر جدول
> الإهجار في [`memory_mode_flag.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/shared/memory_policy/src/memory_mode_flag.cpp#L281).

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
