# المفسّر الشجري (Interpreter)

> **ماذا ستتعلّم:** كيف ينفّذ `InterpreterCore` AST مباشرةً، ويدير النطاقات والدوال والتزامن.

## الدور
`interpreter/` يزور AST ويقيّمه فورًا (tree-walking). الأسرع للتطوير والاختبار، وهو
**المرجع الدلاليّ** الذي يجب أن يطابقه المترجم.

## المكوّنات
| المكوّن | الدور |
|--------|------|
| `InterpreterCore` (`interpreter/include/core/`) | نقطة الدخول؛ يدير التقييم والتنفيذ |
| `ScopeManager` / `VariableManager` | النطاقات والمتغيّرات |
| `FunctionManager` | الدوال (مشترَك read-only بين الخيوط) |
| `StatementExecutor` | تنفيذ الجمل |
| زوّار `interpreter/include/visitors/` | تقييم كل نوع عقدة |
| `interpreter/src/builtins/` | تنفيذ الدوال المضمنة |

## التزامن (Goroutines)
كل goroutine يعمل بـ`StatementExecutor` مستقلّ (مع `ScopeManager`/`VariableManager`/
`OwnershipManager` خاصّين). يُشارَك `FunctionManager` فقط (read-only). المتغيّرات تُلتقَط
كـsnapshot عبر `captureVisibleVariables()`. القنوات آمنة عبر mutex داخليّ في `SadChannel`.

## القيم في وقت التشغيل
كل قيمة `Value` (`shared/types/include/value.h`) — `std::variant` على `ValueType`،
و`OBJECT` يحمل `shared_ptr<ObjectInstance>` للتمرير بالمرجع. → [نظام الأنواع](../systems/types.md).

## الدوال المضمنة
~21 دالة تلقائيّة (اطبع/طول/نوع/رقم/…) + طرق على الأنواع، وبقيّتها عبر وحدات تُستورَد.
التنفيذ في `interpreter/src/builtins/builtin_*.cpp`. → [الدوال المضمنة](../systems/builtins.md).

## التشخيص
- شغّل `.ص` مباشرةً بـ`sad.exe` لاختبار سريع.
- إن طابق المفسّر وخالف المترجم ⇒ المشكلة في SIR/LLVM (BF-08).

---
**اقرأ بعده:** [التمثيل الوسيط SIR](sir.md).
