/* ============================================================================
   تكبير/تصغير خطّ المحتوى — يُضيف أزرار (أ−/إعادة/أ+) إلى شريط القوائم،
   ويحفظ التفضيل في localStorage. يعمل عبر المتغيّر CSS --sad-font-scale.
   يُحمَّل عبر additional-js في book.toml.
   ============================================================================ */
(function () {
  "use strict";
  var KEY = "sad-font-scale";
  var MIN = 0.8, MAX = 1.8, STEP = 0.1, DEFAULT = 1.0;

  function clamp(v) { return Math.min(MAX, Math.max(MIN, Math.round(v * 100) / 100)); }

  function apply(scale) {
    document.documentElement.style.setProperty("--sad-font-scale", scale);
    try { localStorage.setItem(KEY, String(scale)); } catch (e) {}
    var pct = Math.round(scale * 100);
    var label = document.getElementById("sad-font-scale-label");
    if (label) label.textContent = pct + "%";
  }

  function current() {
    var v = parseFloat(localStorage.getItem(KEY));
    return isNaN(v) ? DEFAULT : clamp(v);
  }

  function makeBtn(id, title, html) {
    var b = document.createElement("button");
    b.id = id;
    b.className = "icon-button sad-font-btn";
    b.type = "button";
    b.title = title;
    b.setAttribute("aria-label", title);
    b.innerHTML = html;
    return b;
  }

  function init() {
    // استعادة التفضيل المحفوظ
    apply(current());

    var bar = document.querySelector(".menu-bar .right-buttons") ||
              document.querySelector(".menu-bar");
    if (!bar) return;

    var group = document.createElement("div");
    group.className = "sad-font-zoom";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "حجم الخطّ");

    var dec = makeBtn("sad-font-dec", "تصغير الخطّ", "أ−");
    var label = document.createElement("span");
    label.id = "sad-font-scale-label";
    label.className = "sad-font-label";
    label.title = "إعادة الحجم الافتراضيّ";
    label.style.cursor = "pointer";
    var inc = makeBtn("sad-font-inc", "تكبير الخطّ", "أ+");

    dec.addEventListener("click", function () { apply(clamp(current() - STEP)); });
    inc.addEventListener("click", function () { apply(clamp(current() + STEP)); });
    label.addEventListener("click", function () { apply(DEFAULT); });

    // الترتيب البصريّ: أ−  النسبة  أ+
    group.appendChild(dec);
    group.appendChild(label);
    group.appendChild(inc);
    bar.appendChild(group);

    apply(current()); // لتحديث نصّ النسبة

    // اختصارات لوحة المفاتيح: Ctrl + = / - / 0
    document.addEventListener("keydown", function (e) {
      if (!e.ctrlKey) return;
      if (e.key === "+" || e.key === "=") { apply(clamp(current() + STEP)); e.preventDefault(); }
      else if (e.key === "-") { apply(clamp(current() - STEP)); e.preventDefault(); }
      else if (e.key === "0") { apply(DEFAULT); e.preventDefault(); }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
