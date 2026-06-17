# نظام الأنواع (Value / SadType)

> **ماذا ستتعلّم:** كيف تُمثَّل القيم وقت التشغيل، ونظام الأنواع، والفرق عن أنواع AST.

## قيم وقت التشغيل: `Value`
`shared/types/include/value.h` يعرّف `Value` — النوع الموحّد للقيم وقت التنفيذ:
- `std::variant` على `ValueType` (رقم، عشري، نص، منطقي، مصفوفة، خريطة، كائن، عدم، …).
- `OBJECT` يحمل `shared_ptr<ObjectInstance>` ⇒ **تمرير بالمرجع** للكائنات.
- تجنّب تعارض ماكرو `VOID` مع Windows (يُلغى تعريفه قبل `ValueType::VOID`).

## نظام الأنواع الثابت: `SadType` / `SadTypeKind`
- `SadTypeKind` تعداد لأنواع اللغة (Integer/Float/String/Boolean/Void/Array/Map/Class/Optional/Unknown).
- `SadTypePtr` (من `SadTypeRegistry`) يمثّل أنواعًا مركّبة تحفظ معاملاتها (مثل `مصفوفة<T>`، `خريطة<K,V>`).
- المحلل النحوي ينتج النوع عبر `parseType()`/`parseTypeCore()` (يُرجع `SadTypeKind`) و`parseSadType()` (يُرجع `SadTypePtr` بمعاملات مخزَّنة).

## ملاحظات للمطوّر
- **`DataType` enum لا يحوي `ANY`** — استخدم `DT::OBJECT` بدلًا منه.
- الأنواع المدمجة (رقم/نص/…) **مُعرّفات سياقيّة** لا كلمات محجوزة — تُعرَّف عبر `isTypeToken()` مع lookahead.
- القسمة `/` تُعطي عشريًّا دائمًا — استخدم `رقم(ن/م)` للقسمة الصحيحة.

## مرجع SoT
الأنواع المدمجة مُكتلَجة في `language-truth/types.yaml`. → [language-truth](../sot/language-truth.md).
تفاصيل SIR/الأنواع في `compiler/include/frontend/sir_types.h` → [SIR](../backend/sir.md).

---
**اقرأ بعده:** [نظام الأخطاء](errors.md).
