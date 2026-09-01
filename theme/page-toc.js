/* ============================================================================
   فهرسُ الصفحة (في هذه الصفحة) — يبني قائمةَ عناوينِ h2/h3 للفصل المفتوح
   ويضعها بعد عنوانِ الصفحة مباشرةً. شريطُ mdBook الجانبيّ يعرض عناوينَ الفصول
   لا عناوينَ الأقسام، فالفصولُ الطويلة تُقرأ جدارًا بلا مسح.
   بلا تبعيّةٍ خارجيّة ولا معالجٍ مسبق (mdbook-toc غير مستعمَل عمدًا: يُضيف
   تبعيّةَ cargo إلى CI ويكتب الفهرسَ في HTML المبنيّ فيقيسه lychee).
   يُحمَّل عبر additional-js في book.toml.
   ============================================================================ */
(function () {
  "use strict";

  var MIN_HEADINGS = 4;      // (AR) أقلّ من ذلك: الفصلُ يُمسَح بلا فهرس
  var COLLAPSE_WIDTH = 900;  // (AR) تحت هذا العرض يبدأ الفهرسُ مطويًّا

  // (AR) عنوانٌ صالحٌ للفهرسة: له مُعرِّفٌ يولّده mdBook، ولا يُدرَج h3 قبل أوّل h2.
  function collect(main) {
    var nodes = main.querySelectorAll("h2[id], h3[id]");
    var out = [], sawH2 = false, i;
    for (i = 0; i < nodes.length; i++) {
      var h = nodes[i];
      if (h.tagName === "H2") sawH2 = true;
      else if (!sawH2) continue;
      var text = (h.textContent || "").replace(/\s+/g, " ").trim();
      if (!text) continue;
      out.push({ id: h.id, text: text, level: h.tagName === "H2" ? 2 : 3 });
    }
    return out;
  }

  function build(items) {
    var box = document.createElement("details");
    box.className = "page-toc";
    box.open = window.innerWidth >= COLLAPSE_WIDTH;

    var head = document.createElement("summary");
    head.textContent = "في هذه الصفحة";
    box.appendChild(head);

    var list = document.createElement("ul");
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var li = document.createElement("li");
      li.className = "page-toc-l" + it.level;
      var a = document.createElement("a");
      // (AR) مرساةٌ خام لا مُرمَّزة: مُعرِّفاتُ mdBook عربيّةٌ حرفيّةٌ في HTML، وروابطُ
      //      العناوين التي يولّدها mdBook نفسُها خامّة (`href="#لماذا-خلفيّةٌ-ثالثة"`)
      //      — فالمطابقةُ اتّساقٌ مع الصفحة لا اجتهادُ ترميز.
      a.setAttribute("href", "#" + it.id);
      a.textContent = it.text;
      li.appendChild(a);
      list.appendChild(li);
    }
    box.appendChild(list);
    return box;
  }

  function init() {
    var main = document.querySelector(".content main");
    if (!main || main.querySelector(".page-toc")) return;

    // (AR) صفحةُ الطباعة (`print.html`) تلصق كلَّ الفصول في `main` واحد: ٣٣ عنوانَ h1
    //      و١٨٣ عنوانَ h2/h3 بمُعرِّفاتٍ قد تتكرّر — فهرسٌ واحدٌ عملاقٌ بمراسٍ ملتبسة.
    //      علامةُ الصفحة: أكثرُ من h1 واحدٍ في `main`.
    var h1s = main.querySelectorAll("h1");
    if (h1s.length !== 1) return;

    var items = collect(main);
    if (items.length < MIN_HEADINGS) return;

    // (AR) الموضعُ: بعد كتلةِ العنوان. h1 ليس دائمًا ابنًا مباشرًا لـ`main`:
    //      في `introduction.md` هو داخل `div.hero`، فالإدراجُ عند `main.firstChild`
    //      كان يضعُ الفهرسَ *فوق* لافتةِ الهبوط. نصعدُ إلى أعلى سلفٍ تحت `main`.
    var anchor = h1s[0];
    while (anchor && anchor.parentNode !== main) anchor = anchor.parentNode;
    var box = build(items);
    if (anchor && anchor.nextSibling) main.insertBefore(box, anchor.nextSibling);
    else if (anchor) main.appendChild(box);
    else main.insertBefore(box, main.firstChild);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
