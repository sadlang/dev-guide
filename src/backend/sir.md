# التمثيل الوسيط SIR

> **ماذا ستتعلّم:** ما هو SIR، ولماذا طبقة وسيطة بين AST وLLVM، وأين تعليماته.

## ما هو SIR؟
**SIR (Sad Intermediate Representation)** تمثيل وسيط يبنيه `SIRBuilder` من AST قبل
توليد LLVM IR. يفصل دلالة لغة ص (الملكية، الأنواع، تدفّق التحكّم) عن تفاصيل LLVM.

## لماذا طبقة وسيطة؟
- **تحسين مستقلّ:** `SIROptimizer` يطبّق تمريرات على SIR.
- **تشخيص أسهل:** SIR dumps أوضح من LLVM IR الخام.
- **عزل:** تغيير الواجهة الخلفيّة (LLVM) لا يَمَسّ منطق بناء SIR.
- **دلالة الملكية:** SIR يدعم تعليمات ملكية (ownership) خاصّة بلغة ص.

## الملفّات
| الملف | المحتوى |
|------|---------|
| `compiler/include/frontend/sir_types.h` | تعداد `SIROpcode` + أنواع SIR (الملكية) |
| `compiler/src/frontend/` | `SIRBuilder` (AST → SIR) + `SIROptimizer` |

## الموضع في الخطّ
```mermaid
flowchart LR
  AST --> SB["SIRBuilder"] --> SIR["وحدة SIR"]
  SIR --> SO["SIROptimizer"] --> SIR2["SIR محسَّن"]
  SIR2 --> CG["LLVMCodeGen"] --> IR["LLVM IR"]
```

## إضافة opcode (الإجراء)
1. أضف `SIROpcode::NEW_OP` إلى `sir_types.h` (**إضافة** فقط — لا تغيّر معنى موجود، CW-24).
2. أنتجه في `SIRBuilder` من العقدة المعنيّة.
3. ترجمه في `compiler/src/backend/llvm/`.
4. اختبار مزدوج (مفسّر + مترجم بنفس المخرَج).

## قواعد دقيقة
- **ترتيب الحقول:** يُحدَّد في `SIRBuilder` (حيث تُبنى البنية) — أصلِح أخطاء الترتيب هنا، لا في codegen (BF-10).
- **لا اقتطاع صامت:** كل تحويل نوع يمرّ عبر دالة مُسمّاة (CW-14).

---
**اقرأ بعده:** [توليد LLVM](llvm.md).
