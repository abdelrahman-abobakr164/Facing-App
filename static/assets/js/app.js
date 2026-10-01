/* UI behaviour only. No data lives here: all content comes from your HTML / Django templates. */
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* Theme toggle (also syncs Bootstrap components) */
  $$('[data-theme-toggle]').forEach(b => b.addEventListener('click', () => {
    const t = document.documentElement.dataset.bsTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.bsTheme = t; try { localStorage.theme = t; } catch {}
  }));

  /* Photo / video preview.  data-preview="#el" -> image or background target; otherwise uses the form's .preview box */
  $$('input[type=file]').forEach(inp => inp.addEventListener('change', () => {
    const f = inp.files[0]; if (!f) return; const url = URL.createObjectURL(f);
    if (inp.dataset.preview) {
      const t = $(inp.dataset.preview);
      if (t.tagName === 'IMG') t.src = url; else { t.style.backgroundImage = `url(${url})`; if (t.classList.contains('av')) t.textContent = ''; }
      return;
    }
    const box = $('.preview', inp.form); if (!box) return;
    const vid = f.type.startsWith('video/'), img = $('img', box), video = $('video', box);
    box.classList.remove('d-none'); img.classList.toggle('d-none', vid); video.classList.toggle('d-none', !vid);
    (vid ? video : img).src = url;
  }));
  $$('[data-clear]').forEach(b => b.addEventListener('click', () => {
    const form = b.closest('form'); $$('input[type=file]', form).forEach(i => i.value = ''); $('.preview', form).classList.add('d-none');
  }));

  /* Story draft (create story modal) */
  $$('input[name=bg]').forEach(r => r.addEventListener('change', () => $('.story-draft').style.background = r.value));
  const cap = $('#storyCaption'); if (cap) cap.addEventListener('input', () => $('.draft-text').textContent = cap.value);

  /* Generic buttons */
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-toggle]');           // data-toggle="Follow|Following"
    if (t) { const [a, b] = t.dataset.toggle.split('|'); const on = t.textContent.trim() === a;
      t.textContent = on ? b : a; t.classList.toggle('btn-brand', !on); t.classList.toggle('btn-soft', on); }
    const d = e.target.closest('[data-dismiss]');           // remove a card / row
    if (d) { const el = d.closest('.removable'); el.style.transition = 'opacity .25s'; el.style.opacity = 0; setTimeout(() => el.remove(), 250); }
    const a = e.target.closest('[data-accept]');            // friend request accepted
    if (a) a.closest('.req-actions').innerHTML = '<span class="chip w-100 justify-content-center"><i class="bi bi-check2"></i> Friends now</span>';
    const l = e.target.closest('.like');                    // like (UI only; wire to Django)
    if (l) { const on = l.classList.toggle('active'), n = $('span', l);
      $('i', l).className = 'bi bi-heart' + (on ? '-fill' : ''); n.textContent = +n.textContent + (on ? 1 : -1); }
    const c = e.target.closest('.js-comment');
    if (c) $('.comments', c.closest('article')).classList.toggle('d-none');
  });

  /* Remove current media: dim the current photo/video so the user sees it will be deleted */
  $$('[data-remove-media]').forEach(c => c.addEventListener('change', () => $(c.dataset.removeMedia).classList.toggle('removed', c.checked)));

  /* Messages panel: navbar icon toggles it, a user opens the chat, Esc = back to the list, Esc again = close */
  const mp = $('#msgPanel'), mt = $('#msgToggle');
  if (mp && mt) {
    const lobby = $('.msg-lobby', mp), chats = $$('.msg-conv', mp), dot = $('.dot', mt);
    const showList = () => { chats.forEach(c => c.classList.add('d-none')); lobby.classList.remove('d-none'); };
    const openChat = sel => { lobby.classList.add('d-none'); chats.forEach(c => c.classList.toggle('d-none', '#' + c.id !== sel));
      const box = $(sel + ' .chat-box', mp); box.scrollTop = box.scrollHeight; $(sel + ' input', mp).focus(); };
    const setOpen = on => { mp.classList.toggle('d-none', !on); mt.setAttribute('aria-expanded', on); if (on) showList(); };
    mt.addEventListener('click', () => setOpen(mp.classList.contains('d-none')));
    $$('[data-msg-close]', mp).forEach(b => b.addEventListener('click', () => setOpen(false)));
    $$('[data-msg-back]', mp).forEach(b => b.addEventListener('click', showList));
    $$('[data-chat]', mp).forEach(b => b.addEventListener('click', () => {
      b.classList.remove('unread'); if (dot && !$('.msg-item.unread', mp)) dot.remove(); openChat(b.dataset.chat); }));
    document.addEventListener('keydown', e => {
      if (e.key !== 'Escape' || mp.classList.contains('d-none')) return;
      const sv = $('#storyViewer'); if (sv && !sv.classList.contains('d-none')) return;   // story viewer handles its own Esc
      lobby.classList.contains('d-none') ? showList() : setOpen(false);
    });
  }

  /* Client-side form hints */
  $$('.needs-validation').forEach(f => f.addEventListener('submit', e => {
    if (!f.checkValidity()) { e.preventDefault(); f.classList.add('was-validated'); }
  }));

  /* Open a tab from the URL hash (e.g. followers.html#following) */
  if (location.hash) { const t = $(`[data-bs-target="${location.hash}"]`); if (t) bootstrap.Tab.getOrCreateInstance(t).show(); }

  /* Story viewer: reads .story-item data attributes from the clicked .story */
  const sv = $('#storyViewer'); if (!sv) return;
  let items = [], i = 0, timer;
  const media = $('.sv-media', sv), bars = $('.sv-bars', sv);
  const close = () => { clearTimeout(timer); sv.classList.add('d-none'); media.innerHTML = ''; document.body.style.overflow = ''; };
  const show = n => {
    clearTimeout(timer); if (n >= items.length) return close(); i = Math.max(n, 0);
    const d = items[i].dataset, vid = d.type === 'video';
    bars.innerHTML = items.map((_, k) => `<span class="${k < i ? 'done' : k === i ? 'run' : ''}"></span>`).join('');
    media.style.background = d.bg || '#000';
    media.innerHTML = d.type === 'image' ? `<img src="${d.src}" alt="">` : vid ? `<video src="${d.src}" autoplay playsinline></video>` : '';
    $('.sv-text', sv).textContent = d.text || ''; $('.sv-time', sv).textContent = d.time || '';
    if (vid) media.firstChild.onended = () => show(i + 1); else timer = setTimeout(() => show(i + 1), 5000);
  };
  $$('.story:not(.add)').forEach(b => b.addEventListener('click', () => {
    items = $$('.story-item', b); $('.sv-user', sv).textContent = b.dataset.user;
    $('.sv-av', sv).innerHTML = $('.av', b).outerHTML; b.classList.add('seen');
    sv.classList.remove('d-none'); document.body.style.overflow = 'hidden'; show(0);
  }));
  $('.prev', sv).onclick = () => show(i - 1); $('.next', sv).onclick = () => show(i + 1); $('.sv-close', sv).onclick = close;
  document.addEventListener('keydown', e => { if (sv.classList.contains('d-none')) return;
    if (e.key === 'Escape') close(); if (e.key === 'ArrowRight') show(i + 1); if (e.key === 'ArrowLeft') show(i - 1); });
})();
