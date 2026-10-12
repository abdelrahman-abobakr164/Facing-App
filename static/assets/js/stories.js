/* ==========================================================================
   Stories — stories.js
   No data lives in this file. Everything comes from the HTML that Django
   renders (data-* attributes). Each module starts only if its root exists:
     [data-st-back]    back links
     [data-st-create]  create page (preview, drag & drop, validation)
     [data-st-viewer]  full-screen story player
   ========================================================================== */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.prototype.slice.call((root || document).querySelectorAll(sel));

  /* ---------- helpers ---------- */

  function csrfToken() {
    const input = $('#st-csrf input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  }

  async function post(url) {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest", // tells the Django views to answer with JSON
        "X-CSRFToken": csrfToken(),
        Accept: "application/json",
      },
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  // Go back if the previous page is ours (and not the create form), else use the fallback URL.
  function leave(fallback) {
    let back = false;
    try {
      if (document.referrer) {
        const ref = new URL(document.referrer);
        back = ref.origin === location.origin && !/\/create\/?$/.test(ref.pathname) && history.length > 1;
      }
    } catch (e) { /* ignore */ }
    if (back) history.back();
    else location.href = fallback || "/";
  }

  function relTime(iso) {
    const t = new Date(iso).getTime();
    if (isNaN(t)) return "";
    const s = Math.max(0, Math.round((Date.now() - t) / 1000));
    if (s < 60) return "now";
    const m = Math.floor(s / 60);
    if (m < 60) return m + "m";
    const h = Math.floor(m / 60);
    if (h < 24) return h + "h";
    return Math.floor(h / 24) + "d";
  }

  /* ---------- back links ---------- */

  function initBack() {
    $$("[data-st-back]").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        leave(a.getAttribute("href"));
      });
    });
  }

  /* ---------- create page ---------- */

  function initCreate() {
    const form = $("[data-st-create]");
    if (!form) return;

    const input = $("[data-input]", form);
    const drop = $("[data-drop]", form);
    const preview = $("[data-preview]", form);
    const holder = $("[data-holder]", form);
    const removeBtn = $("[data-remove]", form);
    const caption = $("[data-caption]", form);
    const counter = $("[data-count]", form);
    const errorBox = $("[data-error]", form);
    const submit = $("[data-submit]", form);
    const maxImage = parseInt(form.dataset.maxImage, 10);
    const maxVideo = parseInt(form.dataset.maxVideo, 10);
    let objectUrl = null;

    const mb = (n) => Math.round(n / 1048576);

    function showError(msg) {
      errorBox.textContent = msg;
      errorBox.hidden = !msg;
    }

    function clearFile() {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = null;
      input.value = "";
      holder.innerHTML = "";
      preview.hidden = true;
      drop.hidden = false;
      submit.disabled = true;
    }

    function setFile(file) {
      showError("");
      const isImage = file.type.indexOf("image/") === 0;
      const isVideo = file.type.indexOf("video/") === 0;
      if (!isImage && !isVideo) { clearFile(); return showError("Please choose a photo or a video."); }
      if (file.size > (isImage ? maxImage : maxVideo)) {
        clearFile();
        return showError("This file is too large. Maximum is " + mb(isImage ? maxImage : maxVideo) + " MB.");
      }
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);

      holder.innerHTML = "";
      let el;
      if (isImage) {
        el = document.createElement("img");
        el.alt = "Story preview";
      } else {
        el = document.createElement("video");
        el.muted = true; el.loop = true; el.autoplay = true; el.playsInline = true; el.controls = true;
      }
      el.src = objectUrl;
      holder.appendChild(el);
      preview.hidden = false;
      drop.hidden = true;
      submit.disabled = false;
    }

    input.addEventListener("change", () => { if (input.files && input.files[0]) setFile(input.files[0]); });
    removeBtn.addEventListener("click", () => { showError(""); clearFile(); });

    ["dragenter", "dragover"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("is-over"); }));
    ["dragleave", "drop"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("is-over"); }));
    drop.addEventListener("drop", (e) => {
      const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!file) return;
      try {
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files; // so the file is really posted with the form
        setFile(file);
      } catch (err) { showError("Drag & drop is not supported here. Click to choose a file."); }
    });

    const paintCount = () => { counter.textContent = caption.value.length + "/" + caption.maxLength; };
    caption.addEventListener("input", paintCount);
    paintCount();

    form.addEventListener("submit", (e) => {
      if (!input.files || !input.files[0]) {
        e.preventDefault();
        return showError("Choose a photo or a video first.");
      }
      submit.classList.add("is-loading");
      setTimeout(() => { submit.disabled = true; }, 0); // after the browser has read the form
    });
  }

  /* ---------- story viewer ---------- */

  function initViewer() {
    const root = $("[data-st-viewer]");
    if (!root) return;

    const IMAGE_MS = 5000;      // how long a photo stays on screen
    const IMAGE_WAIT_MS = 8000; // max wait for a slow photo before moving on
    const HOLD_MS = 200;        // press longer than this = "hold to pause"

    const barsBox = $("[data-bars]", root);
    const touch = $("[data-touch]", root);
    const timeEl = $("[data-time]", root);
    const muteBtn = $("[data-mute]", root);
    const likeBtn = $("[data-like]", root);         // visitors only
    const viewsLink = $("[data-viewers-link]", root); // owner only
    const viewsCount = $("[data-views-count]", root);
    const deleteBtn = $("[data-delete]", root);     // owner only
    const sheet = $("[data-sheet]", root);
    const pill = $("[data-pill]", root);
    const toast = $("[data-toast]", root);
    const closeUrl = root.dataset.closeUrl || "/";

    let slides = $$("[data-st-slide]", root);
    let bars = $$(".st-bar", barsBox);
    let index = 0, progress = 0, lastTs = 0, rafId = 0;
    let imgReady = false, imgWaited = 0;
    let holding = false, userPaused = false, sheetOpen = false, muted = false;
    const marked = new Set();

    const current = () => slides[index];
    const currentVideo = () => (current() ? $("video", current()) : null);
    const isPaused = () => holding || userPaused || sheetOpen || document.hidden;

    /* --- progress bars --- */
    const setBar = (i, v) => { if (bars[i]) bars[i].style.setProperty("--p", v); };
    const paintBars = () => bars.forEach((_, i) => setBar(i, i < index ? 1 : 0));

    /* --- playback sync (pause / resume) --- */
    function sync() {
      const v = currentVideo();
      if (v) {
        if (isPaused()) v.pause();
        else if (!v.ended) v.play().catch(() => {});
      }
      root.classList.toggle("is-holding", holding);
      if (pill) pill.hidden = !userPaused;
    }

    /* --- paint helpers --- */
    function paintLike() {
      if (!likeBtn || !current()) return;
      const on = current().dataset.liked === "1";
      likeBtn.classList.toggle("is-on", on);
      likeBtn.setAttribute("aria-pressed", on ? "true" : "false");
    }
    function paintViews() {
      if (!viewsLink || !current()) return;
      viewsCount.textContent = current().dataset.views;
      viewsLink.href = current().dataset.viewersUrl || "#";
    }
    function paintMute() {
      if (!muteBtn) return;
      muteBtn.classList.toggle("is-muted", muted);
      muteBtn.setAttribute("aria-pressed", muted ? "true" : "false");
    }
    function showToast(msg) {
      if (!toast) return;
      toast.textContent = msg;
      toast.classList.add("is-on");
      clearTimeout(showToast.t);
      showToast.t = setTimeout(() => toast.classList.remove("is-on"), 2600);
    }

    /* --- server calls --- */
    function markSeen(slide) {
      const id = slide.dataset.id;
      if (slide.dataset.own === "1" || slide.dataset.seen === "1" || marked.has(id)) return;
      marked.add(id);
      post(slide.dataset.seenUrl)
        .then(() => { slide.dataset.seen = "1"; })
        .catch(() => marked.delete(id)); // try again next time it is shown
    }

    async function toggleLike() {
      const s = current();
      if (!likeBtn || !s || !s.dataset.likeUrl || s.dataset.busy) return;
      const was = s.dataset.liked === "1";
      s.dataset.busy = "1";
      s.dataset.liked = was ? "0" : "1"; // optimistic
      paintLike();
      if (!was) {
        likeBtn.classList.remove("is-burst");
        void likeBtn.offsetWidth; // restart the animation
        likeBtn.classList.add("is-burst");
      }
      try {
        const data = await post(s.dataset.likeUrl);
        s.dataset.liked = data.liked ? "1" : "0";
        s.dataset.likes = data.likes_count;
      } catch (e) {
        s.dataset.liked = was ? "1" : "0"; // roll back
        showToast("Couldn't update your like. Try again.");
      }
      delete s.dataset.busy;
      if (current() === s) paintLike();
    }

    /* --- media --- */
    function startVideo() {
      const v = currentVideo();
      if (!v) return;
      v.preload = "auto";
      v.muted = muted;
      try { v.currentTime = 0; } catch (e) { /* metadata not ready yet */ }
      v.onended = () => { if (current() && current().contains(v)) next(); };
      if (isPaused()) return;
      const p = v.play();
      if (p && p.catch) {
        p.catch((err) => {
          if (err && err.name === "NotAllowedError") { // browser blocks sound autoplay
            muted = true; v.muted = true; paintMute();
            v.play().catch(() => {});
          }
        });
      }
    }

    function waitForImage() {
      const img = $("img", current());
      if (!img || img.complete) { imgReady = true; return; }
      const slide = current();
      const ready = () => { if (current() === slide) imgReady = true; };
      img.addEventListener("load", ready, { once: true });
      img.addEventListener("error", ready, { once: true });
    }

    function preload(i) {
      const s = slides[i];
      const v = s && $("video", s);
      if (v && v.preload === "none") v.preload = "metadata";
    }

    /* --- navigation --- */
    function show(i) {
      if (!slides.length) return;
      index = Math.max(0, Math.min(i, slides.length - 1));
      progress = 0; lastTs = 0; imgReady = false; imgWaited = 0;

      slides.forEach((s, n) => {
        s.classList.toggle("is-active", n === index);
        const v = $("video", s);
        if (v && n !== index) { v.pause(); try { v.currentTime = 0; } catch (e) { /* ignore */ } }
      });
      paintBars();

      const s = current();
      const isVideo = s.dataset.type === "video";
      if (timeEl) timeEl.textContent = relTime(s.dataset.created);
      if (muteBtn) { muteBtn.hidden = !isVideo; paintMute(); }
      paintLike();
      paintViews();

      if (isVideo) startVideo(); else waitForImage();
      markSeen(s);
      preload(index + 1);
    }

    const next = () => { if (index < slides.length - 1) show(index + 1); else close(); };
    const prev = () => show(index > 0 ? index - 1 : 0);
    function close() { cancelAnimationFrame(rafId); leave(closeUrl); }

    /* --- timer loop --- */
    function tick(ts) {
      rafId = requestAnimationFrame(tick);
      const dt = lastTs ? Math.min(ts - lastTs, 100) : 0; // ignore big gaps (tab switch)
      lastTs = ts;
      if (isPaused() || !current()) return;

      if (current().dataset.type === "video") {
        const v = currentVideo();
        if (v && v.duration) progress = v.currentTime / v.duration; // next() runs on "ended"
      } else {
        if (!imgReady) {
          imgWaited += dt;
          if (imgWaited > IMAGE_WAIT_MS) imgReady = true;
          return;
        }
        progress += dt / IMAGE_MS;
        if (progress >= 1) { setBar(index, 1); next(); return; }
      }
      setBar(index, Math.min(progress, 1));
    }

    /* --- delete (owner) --- */
    function openSheet() {
      sheetOpen = true; sheet.hidden = false; sync();
      const cancel = $("[data-sheet-cancel]", sheet);
      if (cancel) cancel.focus();
    }
    function closeSheet() { sheetOpen = false; sheet.hidden = true; sync(); }

    async function confirmDelete() {
      const s = current();
      const btn = $("[data-sheet-confirm]", sheet);
      if (!s || !s.dataset.deleteUrl) return;
      btn.disabled = true;
      try {
        await post(s.dataset.deleteUrl);
        const i = index;
        s.remove();
        bars[i].remove();
        slides.splice(i, 1);
        bars.splice(i, 1);
        closeSheet();
        btn.disabled = false;
        if (!slides.length) return close();
        show(Math.min(i, slides.length - 1));
      } catch (e) {
        btn.disabled = false;
        closeSheet();
        showToast("Couldn't delete the story. Try again.");
      }
    }

    /* --- input: tap zones, hold to pause, swipe down to close --- */
    let holdTimer = 0, held = false, downX = 0, downY = 0;

    touch.addEventListener("pointerdown", (e) => {
      held = false; downX = e.clientX; downY = e.clientY;
      try { touch.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      holdTimer = setTimeout(() => { held = true; holding = true; sync(); }, HOLD_MS);
    });
    function endPress(e, cancelled) {
      clearTimeout(holdTimer);
      if (held) { holding = false; sync(); }
      if (cancelled) return;
      if (!held && e.clientY - downY > 100 && Math.abs(e.clientX - downX) < 60) return close();
      if (held) return;
      const r = touch.getBoundingClientRect();
      if (e.clientX - r.left < r.width * 0.3) prev(); else next();
    }
    touch.addEventListener("pointerup", (e) => endPress(e, false));
    touch.addEventListener("pointercancel", (e) => endPress(e, true));
    touch.addEventListener("contextmenu", (e) => e.preventDefault());

    $$("[data-close]", root).forEach((b) => b.addEventListener("click", close));
    const prevBtn = $("[data-prev]", root), nextBtn = $("[data-next]", root);
    if (prevBtn) prevBtn.addEventListener("click", prev);
    if (nextBtn) nextBtn.addEventListener("click", next);

    if (muteBtn) {
      muteBtn.addEventListener("click", () => {
        muted = !muted;
        const v = currentVideo();
        if (v) v.muted = muted;
        paintMute();
      });
    }
    if (likeBtn) likeBtn.addEventListener("click", toggleLike);
    if (deleteBtn) deleteBtn.addEventListener("click", openSheet);
    if (sheet) {
      $("[data-sheet-cancel]", sheet).addEventListener("click", closeSheet);
      $("[data-sheet-confirm]", sheet).addEventListener("click", confirmDelete);
      sheet.addEventListener("click", (e) => { if (e.target === sheet) closeSheet(); });
    }

    document.addEventListener("keydown", (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (sheetOpen) { if (e.key === "Escape") closeSheet(); return; }
      switch (e.key) {
        case "ArrowRight": next(); break;
        case "ArrowLeft": prev(); break;
        case " ": e.preventDefault(); userPaused = !userPaused; sync(); break;
        case "Escape": close(); break;
        case "m": case "M": if (muteBtn && !muteBtn.hidden) muteBtn.click(); break;
        case "l": case "L": toggleLike(); break;
        default: return;
      }
    });
    document.addEventListener("visibilitychange", sync);

    /* --- portrait media fills the screen, landscape media stays uncropped --- */
    function fit(el) {
      const w = el.naturalWidth || el.videoWidth, h = el.naturalHeight || el.videoHeight;
      if (w && h) el.classList.toggle("is-portrait", w / h < 0.8);
    }
    slides.forEach((slide) => {
      const el = $("img, video", slide);
      if (!el) return;
      fit(el);
      el.addEventListener(el.tagName === "VIDEO" ? "loadedmetadata" : "load", () => fit(el));
    });

    /* --- start --- */
    show(parseInt(root.dataset.start, 10) || 0);
    rafId = requestAnimationFrame(tick);
  }

  /* ---------- boot ---------- */
  initBack();
  initCreate();
  initViewer();
})();
