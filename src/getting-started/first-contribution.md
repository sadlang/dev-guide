# أوّل مساهمة (Walkthrough)

> **ماذا ستتعلّم:** المسار الكامل لمساهمة صغيرة — من فرع معزول حتى PR إلى `dev`.

نأخذ مثالًا واقعيًّا: **إضافة دالة مضمنة جديدة**. الخطوات تعمّ على أي تغيير.

## 1) افهم الطبقة والتشابك
لا تغيير «معزول». دالة مضمنة تَمَسّ: `language-truth/builtins/` (المصدر) + المُولَّد +
تنفيذ المفسّر + codegen المترجم + اختبار. راجع [الأنظمة المتشابكة](../architecture/interconnected.md).

## 2) أنشئ فرع عمل معزول (worktree من dev)
```bash
cd /c/s_lang/s-programming-language
git fetch origin
git worktree add /c/s_lang/temp-brunch/builtin-جذر -b agent/builtin-جذر origin/dev
cd /c/s_lang/temp-brunch/builtin-جذر
```

## 3) ابدأ من مصدر الحقيقة (لا من الكود المُولَّد)
أضف الدالة إلى `language-truth/builtins/<domain>.yaml`، ثم أعد التوليد:
```bash
python scripts/codegen/gen_all_builtins_yaml.py   # أو المولّد المعنيّ
```

## 4) نفّذ في الطبقة الصحيحة
- المفسّر: `interpreter/src/builtins/builtin_*.cpp`.
- المترجم: `compiler/src/backend/llvm/builders/builtins/*.cpp`.

## 5) اكتب اختبار `.ص` (إيجابيّ + سلبيّ)
ملف تحت `tests/` بصيغة `@expected` الصحيحة.

## 6) ابنِ وشغّل (تنفيذ مزدوج)
```bash
cmake --build build --config Debug --target sad
cmake --build build --config Release --target sadc
python runner.py --level P1        # يجب أن يمرّ 100% بلا تراجع
```

## 7) أودِع (موقّع GPG) وافتح PR
```bash
git add -A
git commit -m "feat(builtins): دالة جذر(...)"     # موقّع تلقائيًّا
git push -u origin agent/builtin-جذر
gh pr create --base dev --title "إضافة جذر" --body "قائمة الملفات + نتائج runner"
```

## 8) نظّف بعد الدمج
```bash
cd /c/s_lang/s-programming-language
git worktree remove /c/s_lang/temp-brunch/builtin-جذر
git branch -D agent/builtin-جذر
```

> ✅ راجع [معيار الإنجاز](../contributing/definition-of-done.md) قبل إعلان الانتهاء.

---
**اقرأ بعده:** [خريطة المستودع](repo-map.md).
