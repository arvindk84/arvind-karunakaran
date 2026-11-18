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
    var isOpen = function () { return toggle.getAttribute("aria-expanded") === "true"; };
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      doc.documentElement.classList.toggle("nav-open", open); /* scroll lock, see site.css */
    };
    toggle.addEventListener("click", function () { setOpen(!isOpen()); });
    doc.addEventListener("keydown", function (e) {
      if (e.key !== "Escape" || !isOpen()) return;
      var hadFocus = nav.contains(doc.activeElement);
      setOpen(false);
      if (hadFocus) toggle.focus(); /* focus would otherwise be lost inside the hidden menu */
    });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    /* Tabbing out of the open menu (past the last link, or back past the toggle) closes it,
       so keyboard focus never lands on the dimmed page while the menu still covers it */
    var onFocusOut = function (e) {
      var to = e.relatedTarget;
      if (isOpen() && to && !nav.contains(to) && !toggle.contains(to)) setOpen(false);
    };
    nav.addEventListener("focusout", onFocusOut);
    toggle.addEventListener("focusout", onFocusOut);
    /* A tap on the dimmed page closes the menu and does nothing else (it does not follow a link underneath) */
    doc.addEventListener("click", function (e) {
      if (!isOpen() || nav.contains(e.target) || toggle.contains(e.target)) return;
      if (!(header && header.contains(e.target))) { e.preventDefault(); e.stopPropagation(); } /* the wordmark still works */
      setOpen(false);
    }, true);
    /* Rotating or resizing to the desktop layout closes the menu and releases the scroll lock */
    var desktop = window.matchMedia ? window.matchMedia("(min-width: 940px)") : null;
    if (desktop) {
      var onBp = function () { if (desktop.matches && isOpen()) setOpen(false); };
      if (desktop.addEventListener) desktop.addEventListener("change", onBp); else if (desktop.addListener) desktop.addListener(onBp);
    }
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
      var c = doc.createElement("span"); c.className = "count"; c.textContent = n; c.setAttribute("aria-hidden", "true"); btn.appendChild(c);
      var sr = doc.createElement("span"); sr.className = "sr-only"; sr.textContent = ", " + n + (n === 1 ? " item" : " items"); btn.appendChild(sr);
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
    btn.setAttribute("aria-live", "polite"); /* screen readers hear "Copied" */
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
    subnav.querySelectorAll('ul a[href^="#"]').forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    var current = null;
    var firstId = Object.keys(links)[0];
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && links[en.target.id]) {
          if (current) current.classList.remove("is-active");
          current = links[en.target.id];
          current.classList.add("is-active");
          var ul = current.closest("ul");
          if (ul && ul.scrollWidth > ul.clientWidth) {
            /* Measure against the scroller itself (offsetLeft is relative to the sub-nav and left
               the active item half cut off on phones). Keep the previous item's edge in view. */
            var left = ul.scrollLeft + current.getBoundingClientRect().left - ul.getBoundingClientRect().left - 28;
            var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            ul.scrollTo({ left: Math.max(0, left), behavior: calm ? "auto" : "smooth" });
          }
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(links).forEach(function (id) { var s = doc.getElementById(id); if (s) io.observe(s); });
    /* Back above the first section (hero, logos), by scrolling or a jump to the top: nothing is highlighted */
    var firstEl = doc.getElementById(firstId), queued = false;
    var clearAtTop = function () {
      queued = false;
      if (current && firstEl && firstEl.getBoundingClientRect().top > window.innerHeight * 0.3) { current.classList.remove("is-active"); current = null; }
    };
    window.addEventListener("scroll", function () { if (!queued) { queued = true; window.requestAnimationFrame(clearAtTop); } }, { passive: true });
    /* Fade an edge only while there is more to scroll that way */
    var sul = subnav.querySelector("ul");
    if (sul) {
      var onX = function () {
        sul.classList.toggle("fade-l", sul.scrollLeft > 4);
        sul.classList.toggle("fade-r", sul.scrollLeft + sul.clientWidth < sul.scrollWidth - 4);
      };
      sul.addEventListener("scroll", onX, { passive: true });
      window.addEventListener("resize", onX);
      onX();
    }
  }
})();
