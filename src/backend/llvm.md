# توليد LLVM (المترجم `sad-build`)

> **ماذا ستتعلّم:** كيف يحوّل `LLVMCodeGen` تمثيل SIR إلى LLVM IR ثم ملفّ تنفيذيّ أصليّ.

## الدور
`compiler/src/backend/llvm/` يأخذ SIR المحسَّن ويُنتج LLVM IR، ثم يستخدم LLVM لتوليد
كائن ثم ربطه في ملفّ تنفيذيّ. هذا قلب المترجم `sad-build`.

## الاعتماد على LLVM
- **LLVM 18** — مفعّل بشرط `ENABLE_LLVM_BACKEND=ON`؛ راجع `cmake/llvm.cmake` و`#ifdef HAS_LLVM`.
- واجهة المترجم تعيش في `tools/compiler/` (`compiler_driver_*.cpp`)، وهدفُها `sad-build`
  (`sad-build.exe`). أمّا `sadc.exe` فاسمٌ متقاعد لا يُنتجه أيّ هدف.

> ⚠️ **علَمٌ عربيٌّ قانونيٌّ وحيد — لا مرادف لاتينيّ.** أعلامُ المترجم الطويلة كلُّها
> في [`language-truth/cli_flags.yaml`](https://github.com/sadlang/s-programming-language/blob/dev/language-truth/cli_flags.yaml)،
> ونصُّه صريح: «اسمٌ عربيٌّ قانونيٌّ وحيد، بلا مرادفات ولا توافقٍ خلفيّ». فمخرجاتُ
> LLVM الوسيطة هي `--أظهر-llvm` و`--أظهر-bc` — و`--emit-llvm` **لا تُقبَل**. تبقى
> الأعلامُ القصيرة الموروثة من سلسلة الأدوات (`-o -c -S -g -O* -L -l -Werror -T -h`)
> أعرافًا في المحلِّل، خارجَ هذا المصدر — بنصّ المصدر نفسِه: «النطاق = الأعلام الطويلة فقط».

> 📎 **لا سقوطَ صامتًا حين تغيب LLVM.** إلى جانب `sad-build` يُبنى **دائمًا** هدفٌ
> ثانٍ نحيلٌ بلا LLVM البتّة: `sad-build-native`. وهو لا يفترق عن أخيه إلّا في ملفٍّ
> واحد — [`compiler_driver_backend_llvm_absent.cpp`](https://github.com/sadlang/s-programming-language/blob/dev/tools/compiler/compiler_driver_backend_llvm_absent.cpp)
> بدل `compiler_driver_backend.cpp` — الذي **يرفض** صراحةً كلّ طلبٍ لأثرٍ من صنع
> LLVM برمز الكتالوج `INT_LLVM_PATH_ABSENT`، بدل تسليم أثرٍ من
> [الخلفيّة الأصليّة](native.md) وكأنّه هو. مَن طلب أثرًا بعينه يُعطاه أو يُرَدّ.
>
> ولاحظ **لماذا وحدةُ ترجمةٍ كاملةٌ لا فرعُ `#ifdef`**: الفرعُ الذي لا يُصرَّف في أكثر
> الخانات ينجرف صامتًا عن أخيه — وهو عطبٌ مقيسٌ في هذا المستودع من قبل. فكلُّ سطرٍ
> هنا يُصرَّف على المنصّات الثلاث وفي التكوينَين.

## البناة (builders)
`compiler/src/backend/llvm/builders/` — **ثمانية مجلّداتٍ** مقيسةٍ على `dev`، مولِّدٌ
لكلّ عائلة: `core` · `arithmetic` · `collections` · `oop` · `memory` · `directives`
(توجيهات `@`) · `platform` · `builtins` (الدوالّ المضمنة).

## مخطّط
```mermaid
flowchart LR
  SIR["SIR محسَّن"] --> CG["LLVMCodeGen + builders"]
  CG --> IR["LLVM IR"]
  IR --> OBJ["كائن (LLVM)"]
  OBJ --> LINK["ربط"]
  LINK --> EXE["تنفيذيّ أصليّ"]
```

## التشخيص (BF-07)
عند خطأ في المترجم، ولّد IR بـ`--أظهر-llvm` وافحص:
- هل الكتلة الأولى (entry block) صحيحة؟
- هل أنواع الحقول والمعاملات متّسقة؟
- هل ترتيب التعليمات يحترم تبعيّات البيانات؟
- هل `getelementptr` يستخدم الفهارس الصحيحة؟

## قواعد codegen مهمّة
- **أسماء كتل واصفة:** `precond_fail`, `loop_body`, `then_block` — لا `bb1`/`label2` (CW-11).
- **الترتيب يكسر الدلالة:** ترتيب أبجديّ لأسماء الكتل يكسر ترتيب التنفيذ — استخدم `std::vector` محافظًا على ترتيب الإدراج (CW-27).
- **أصلِح في الطبقة الصحيحة:** خطأ تحويل أنواع يُصلَح في codegen؛ خطأ ترتيب حقول في `SIRBuilder` (BF-10).

---
**اقرأ بعده:** [الخلفيّة الأصليّة بلا LLVM](native.md).
