# نظام الأخطاء والتشخيص

> **ماذا ستتعلّم:** كيف تُعرَّف الأخطاء وتُطلَق وتُعرَض، وكيف تضيف رمز خطأ جديدًا.

## المبدأ
الأخطاء **مكتلَجة كمصدر موحّد**: رموزها ورسائلها (عربيّة/إنجليزيّة) وتلميحات الإصلاح
تعيش في `language-truth/errors/` (مصدر V5)، ويُولَّد منها كود C++ والتشخيص.

## الملفّات
| الملف | المحتوى |
|------|---------|
| `language-truth/errors/<cat>.yaml` | **المصدر** — رموز ورسائل وتلميحات |
| `shared/errors/include/error_codes.h` | تعداد `ErrorCode` |
| `shared/errors/generated/*` | **مُولَّد** عند البناء |
| `_schemas/error.schema.json` | مخطّط التحقّق |

## الإطلاق (لا نصوص حرّة)
> أطلِق الأخطاء بـ`ErrorCode::<NAME>` + placeholders عبر الكتالوج الموحّد.
> **يُمنع** نصّ خطأ حرّ (`runtime_throw.h`) أو `throw std::runtime_error` (نمط مهجور).

نمط معالجة موحّد لكل طبقة: `reportError()` في codegen · exceptions في المحلل النحوي ·
error codes في FFI (CW-22).

## العرض
`ErrorManager` يُجمِّع التشخيصات ويطبعها بلغتين مع الموقع (سطر/عمود) واقتباس المصدر.

## إضافة رمز خطأ (الإجراء)
1. أضف الرمز/الرسالة إلى `language-truth/errors/<cat>.yaml`.
2. أضف `ErrorCode::<NAME>` إلى `error_codes.h` إن لزم.
3. أعد التوليد (`gen_error_messages.py` / عبر البناء).
4. أطلِقه من الطبقة الصحيحة بـ`ErrorCode::<NAME>` + placeholders.
5. اكتب اختبارًا سلبيًّا (`@expected` خطأ).

> راجع بنى YAML للأخطاء والهجرة V4→V5 في مهارة `sad-lang-dev` (`references/error-yaml-structures.md`).

---
**اقرأ بعده:** [الدوال المضمنة](builtins.md).
