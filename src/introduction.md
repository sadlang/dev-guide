<div class="hero">
  <h1>دليل مطوّري لغة ص</h1>
  <p class="tagline">الأنظمة الداخلية — من المصدر إلى التنفيذ</p>
  <p>كيف تعمل لغة ص من الداخل، وكيف تُسهم في تطويرها بثقة: معجمي → نحوي → AST → مفسّر/مترجم، فوق مصدر حقيقة موحّد.</p>
</div>

> **لمن هذا الدليل؟** لمن يطوّر **لغة ص نفسها** (المفسّر، المترجم `sadc`، الأنظمة الداخلية) —
> لا لمن يكتب برامج *بها*. إن كنت تكتب `.ص` فهذا الدليل ليس لك.

## ابدأ من هنا

<div class="cards">
  <a class="card" href="getting-started/setup.html">
    <span class="ico">⚙️</span><span class="t">البدء</span>
    <span class="d">إعداد البيئة، البناء، وأوّل مساهمة.</span>
  </a>
  <a class="card" href="architecture/overview.html">
    <span class="ico">🗺️</span><span class="t">المعمارية</span>
    <span class="d">الطبقات وخطّ الأنابيب والتشابك.</span>
  </a>
  <a class="card" href="sot/philosophy.html">
    <span class="ico">⭐</span><span class="t">مصدر الحقيقة <span class="badge-star">يميّزنا</span></span>
    <span class="d">النظام المدفوع بالبيانات (data-driven).</span>
  </a>
  <a class="card" href="frontend/lexer.html">
    <span class="ico">🔤</span><span class="t">الواجهة الأماميّة</span>
    <span class="d">المعجمي · النحوي · AST.</span>
  </a>
  <a class="card" href="backend/interpreter.html">
    <span class="ico">⚡</span><span class="t">الواجهة الخلفيّة</span>
    <span class="d">المفسّر · SIR · LLVM · VM.</span>
  </a>
  <a class="card" href="contributing/workflow.html">
    <span class="ico">🌿</span><span class="t">المساهمة</span>
    <span class="d">فروع dev · worktrees · PR موقّع.</span>
  </a>
</div>

## فلسفة لغة ص الداخلية في سطور
- **معماريّة طبقيّة صارمة:** `Lexer → Parser → AST → (Interpreter | SIR → LLVM)`. كل طبقة تعتمد فقط على ما تحتها.
- **مدفوعة بالبيانات (data-driven):** بيانات اللغة **وقواعدها النحويّة** تعيش في `language-truth/` كمصدر موحّد (YAML)، ويُولَّد منها كود C++ والتوثيق. **هذا جوهر تميّزنا.**
- **عربيّة أصيلة:** الكلمات المفتاحيّة والمعرّفات بالعربية، UTF-8، والكتل تُغلَق بـ«نهاية».
- **تنفيذ مزدوج:** كل ميزة تعمل في المفسّر **والمترجم** (أو تُعفى صراحةً).

## كيف يختلف عن `rustc-dev-guide`؟
استلهمنا أفضل ما فيه (mdBook، التتبّع للكود، فصل المساهمة) وأضفنا طبقةً لا يملكها:

```mermaid
flowchart LR
  subgraph sad["دليل لغة ص"]
    S1["language-truth/*.yaml<br/>مصدر موحّد"] --> S2["codegen<br/>gen_*.py"]
    S2 --> S3["كود C++ مُولَّد"]
    S1 --> S4["توثيق + مخطّطات مُولَّدة"]
  end
```

مصدر حقيقة موحّد للقواعد والبيانات · توثيق مُولَّد لا يتقادم · مخطّطات Mermaid منهجيّة ·
سير مساهمة حديث (worktrees + فرع `dev` محميّ + PR موقّع GPG).

---
**اقرأ بعده:** [إعداد البيئة والبناء](getting-started/setup.md) · أو تصفّح [حالة الدليل](status.md).
