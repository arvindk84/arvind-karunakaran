/* site.js · small progressive enhancements. Every page works without it. */
(function () {
  "use strict";
  var doc = document;

  /* Header border once the page scrolls */
  var header = doc.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Mobile nav */
  var toggle = doc.querySelector(".nav-toggle");
  var nav = doc.getElementById("site-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    };
    toggle.addEventListener("click", function () { setOpen(toggle.getAttribute("aria-expanded") !== "true"); });
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
  }

  /* Publication filters: buttons[data-filter] toggle .pub[data-type] */
  doc.querySelectorAll("[data-filter-group]").forEach(function (group) {
    var list = doc.getElementById(group.getAttribute("data-filter-group"));
    if (!list) return;
    var items = list.querySelectorAll("[data-type]");
    var buttons = group.querySelectorAll("[data-filter]");
    buttons.forEach(function (btn) {
      var f = btn.getAttribute("data-filter");
      var n = f === "all" ? items.length : list.querySelectorAll('[data-type="' + f + '"]').length;
      var c = doc.createElement("span"); c.className = "count"; c.textContent = n; btn.appendChild(c);
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
        items.forEach(function (it) { it.hidden = !(f === "all" || it.getAttribute("data-type") === f); });
      });
    });
  });

  /* Video facades: <a class="video" data-embed="https://..."> swaps to an iframe on click.
     playVideo(el, start) also serves jump links; start (seconds) replaces any start= in data-embed. */
  var playVideo = function (el, start) {
    var src = el.getAttribute("data-embed");
    if (start != null) {
      src = /[?&]start=\d+/.test(src) ? src.replace(/([?&]start=)\d+/, "$1" + start)
                                      : src + (src.indexOf("?") > -1 ? "&" : "?") + "start=" + start;
    }
    src += (src.indexOf("?") > -1 ? "&" : "?") + "autoplay=1";
    var f = el.querySelector("iframe");
    if (!f) {
      f = doc.createElement("iframe");
      f.title = el.getAttribute("aria-label") || "Video";
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen";
      f.allowFullscreen = true;
      el.appendChild(f);
    }
    f.src = src;
    el.classList.add("is-playing");
  };
  doc.querySelectorAll(".video[data-embed]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return; /* let people open in a new tab */
      if (el.classList.contains("is-playing")) { e.preventDefault(); return; }
      e.preventDefault();
      playVideo(el);
    });
  });

  /* Jump links: <a data-jump="#video-id" data-start="584" href="watch URL&t=584s"> plays that facade from the given second */
  doc.querySelectorAll("a[data-jump][data-start]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      var el = doc.querySelector(a.getAttribute("data-jump"));
      if (!el || !el.hasAttribute("data-embed")) return; /* fall back to the YouTube link */
      e.preventDefault();
      playVideo(el, parseInt(a.getAttribute("data-start"), 10));
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  /* Copy buttons: <button class="copy-btn" data-copy="#id"> */
  doc.querySelectorAll(".copy-btn[data-copy]").forEach(function (btn) {
    var label = btn.textContent;
    btn.addEventListener("click", function () {
      var src = doc.querySelector(btn.getAttribute("data-copy"));
      if (!src) return;
      var text = src.innerText.trim();
      var done = function () { btn.textContent = "Copied"; btn.classList.add("is-done"); setTimeout(function () { btn.textContent = label; btn.classList.remove("is-done"); }, 1800); };
      var legacy = function () {
        var r = doc.createRange(); r.selectNodeContents(src);
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        var ok = false;
        try { ok = doc.execCommand("copy"); } catch (err) {}
        s.removeAllRanges();
        if (ok) done(); else btn.textContent = "Select and copy";
      };
      if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(done, legacy); }
      else { legacy(); }
    });
  });

  /* Sub-nav scrollspy */
  var subnav = doc.querySelector(".subnav");
  if (subnav && "IntersectionObserver" in window) {
    doc.documentElement.classList.add("has-subnav");
    var links = {};
    subnav.querySelectorAll('a[href^="#"]').forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && links[en.target.id]) {
          if (current) current.classList.remove("is-active");
          current = links[en.target.id];
          current.classList.add("is-active");
          var ul = current.closest("ul");
          if (ul) ul.scrollTo({ left: current.offsetLeft - 24, behavior: "smooth" });
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(links).forEach(function (id) { var s = doc.getElementById(id); if (s) io.observe(s); });
  }
})();
