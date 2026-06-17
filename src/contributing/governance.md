# نظام الحوكمة (BMAD)

> **ماذا ستتعلّم:** متى تنطبق الحوكمة، وما الواجب قبل لمس `_bmad-output/`.

## متى تنطبق؟
عند أي تعديل/إضافة/قراءة في `_bmad-output/` (سياسات، أنظمة، ستوريات، حالة، قرارات)،
أو عند العمل ضمن ستوري محكوم. خارج ذلك، اتبع [سير العمل](workflow.md) و[DoD](definition-of-done.md).

## الملفّات الإلزاميّة للقراءة (بالترتيب)
1. السياسة الأمّ: `_bmad-output/governance/1-policy/planning/PRD.md`.
2. إطار إدارة المشروع: `…/PROJECT_MANAGEMENT_FRAMEWORK.md`.
3. آخر تقرير تحقّق (مصدر الحقيقة للحالة): `…/1-policy/status/VERIFICATION_REPORT_<date>.md`.
4. السبرنت الحالي: `…/sprints/SPRINT_CURRENT.md`.
5. عقد الكود: `…/3-code-contract/planning/prd.md`.

## البنية الموحّدة (لكل نظام)
`planning/` · `epics/` · `stories/` · `sprints/` · `status/` · `decisions/` · `README.md`.

## قواعد سلوكيّة صارمة
- **GR-01:** لا ادّعاء نسب إنجاز بلا أدلة من الكود الفعليّ (grep/build/list).
- **GR-02:** لا تَحذف ADRs — المُلغى يُعلَّم `Superseded` ويُربط بـ`supersededBy`.
- **GR-03:** السبرنت لا ينتهي بلا RETRO.
- **GR-04:** الملفّ الزائف يُعلَّم `OUT-OF-DATE` فورًا (لا حذف للمحتوى التاريخيّ).
- **GR-05:** قبل نظام جديد، انسخ `_TEMPLATE/` بنفس بنية الستة مجلدات.
- **GR-06:** التواريخ من الجهاز فقط (`Get-Date -Format "yyyy-MM-dd"`).

## علامة الإقرار
في أوّل ردّ بعد بدء مهمّة تَمَسّ `_bmad-output/`، اكتب سطرًا صريحًا:
> «قرأت السياسة في `_bmad-output/governance/1-policy/`؛ آخر تقرير تحقّق: `VERIFICATION_REPORT_<YYYY-MM-DD>.md`؛ السبرنت الحالي: `<اسم>`.»

> التفاصيل الكاملة في مهارة `sad-lang-dev` (`references/governance.md`).

---
**اقرأ بعده:** [مسرد المصطلحات](../glossary.md).
