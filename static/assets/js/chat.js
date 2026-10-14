/* ===== Chat (paste into app.js, or load as its own script) ===== */
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const norm = s => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');   // ignores case and accents

  /* ---- Live search + Direct / Group tabs ----
     Search box:  <input data-live-search="#list">      Rows: [data-item] (+ data-type="direct|group")
     Tab buttons: [data-tab="all|direct|group"][data-tab-for="#list"]     Empty message: [data-empty]
     Events are delegated on document, so this works wherever the script is loaded. */
  const applyFilter = list => {
    const input = $(`[data-live-search="#${list.id}"]`), q = norm(input ? input.value.trim() : ''), tab = list.dataset.tab || 'all';
    let shown = 0;
    $$('[data-item]', list).forEach(row => {
      const ok = norm(row.textContent).includes(q) && (tab === 'all' || row.dataset.type === tab);
      row.classList.toggle('d-none', !ok); if (ok) shown++;
    });
    const empty = $('[data-empty]', list); if (empty) empty.classList.toggle('d-none', shown > 0);
    const clear = input && $('.search-clear', input.parentElement); if (clear) clear.classList.toggle('d-none', !input.value);
  };
  document.addEventListener('input', e => {
    const input = e.target.closest('[data-live-search]'); if (!input) return;
    const list = $(input.dataset.liveSearch); if (list) applyFilter(list);
  });
  document.addEventListener('click', e => {
    const tab = e.target.closest('[data-tab]');
    if (tab) {
      const list = $(tab.dataset.tabFor); if (!list) return;
      list.dataset.tab = tab.dataset.tab;
      $$(`[data-tab-for="${tab.dataset.tabFor}"]`).forEach(b => b.classList.toggle('active', b === tab));
      applyFilter(list);
    }
    const clear = e.target.closest('.search-clear');
    if (clear) { const input = $('input', clear.parentElement); input.value = ''; input.focus(); input.dispatchEvent(new Event('input', { bubbles: true })); }
  });

  /* ---- Character counters: <input data-counter="#out" maxlength> ---- */
  $$('[data-counter]').forEach(inp => {
    const out = $(inp.dataset.counter), show = () => { out.textContent = `${inp.value.length}/${inp.maxLength}`; };
    inp.addEventListener('input', show); show();
  });

  /* ---- Group page: photo preview + selected people chips ---- */
  $$('input[type=file][data-preview]').forEach(inp => inp.addEventListener('change', () => {
    const f = inp.files[0], t = $(inp.dataset.preview); if (!f) return;
    t.style.backgroundImage = `url(${URL.createObjectURL(f)})`; t.style.backgroundSize = 'cover'; t.style.backgroundPosition = 'center'; t.textContent = '';
  }));
  const cand = $('#candidates'), chips = $('#selectedChips');
  if (cand && chips) cand.addEventListener('change', () => {
    chips.replaceChildren();
    $$('input:checked', cand).forEach(box => {
      const chip = document.createElement('span'), x = document.createElement('button');
      chip.className = 'sel-chip'; chip.append($('.name', box.closest('.person')).textContent + ' ');
      x.type = 'button'; x.textContent = '×'; x.setAttribute('aria-label', 'Remove');
      x.onclick = () => { box.checked = false; box.dispatchEvent(new Event('change', { bubbles: true })); };
      chip.append(x); chips.append(chip);
    });
    $('#selCount').textContent = chips.children.length;
  });

  /* ---- Chat room ---- */
  const room = $('.chat-room'), box = $('#chatMessages'), jump = $('#jumpLatest');
  if (box) {
    box.scrollTop = box.scrollHeight;
    box.addEventListener('scroll', () => jump.classList.toggle('d-none', box.scrollHeight - box.scrollTop - box.clientHeight < 240));
    jump.addEventListener('click', () => box.scrollTo({ top: box.scrollHeight }));
  }

  const form = $('#composeForm');
  if (form) {
    const ta = $('textarea', form), file = $('input[type=file]', form), send = $('.compose-send', form);
    const prev = $('#attachPreview'), err = $('#attachError'), MAX_MB = { image: 10, video: 50 };
    const update = () => { send.disabled = !ta.value.trim() && !file.files.length; };
    const grow = () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 140) + 'px'; };
    const clear = () => { file.value = ''; prev.classList.add('d-none'); update(); };
    ta.addEventListener('input', () => { grow(); update(); });
    ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!send.disabled) form.requestSubmit(); } });
    $('.attach-x', form).addEventListener('click', () => { clear(); err.classList.add('d-none'); });
    file.addEventListener('change', () => {
      const f = file.files[0]; if (!f) return clear();
      const kind = f.type.startsWith('video/') ? 'video' : f.type.startsWith('image/') ? 'image' : null;
      if (!kind || f.size > MAX_MB[kind] * 1048576) {
        clear(); err.textContent = kind ? `${kind === 'video' ? 'Videos' : 'Photos'} can be up to ${MAX_MB[kind]} MB.` : 'Only photos and videos can be sent.';
        return err.classList.remove('d-none');
      }
      err.classList.add('d-none');
      const url = URL.createObjectURL(f), img = $('img', prev), vid = $('video', prev);
      img.classList.toggle('d-none', kind !== 'image'); vid.classList.toggle('d-none', kind !== 'video');
      (kind === 'image' ? img : vid).src = url; $('.attach-name', prev).textContent = f.name;
      prev.classList.remove('d-none'); update();
    });
    form.addEventListener('submit', () => {                       // spinner while the message is being sent
      send.classList.add('sending'); $('i', send).className = 'bi bi-arrow-repeat';
      setTimeout(() => { send.disabled = true; }, 0);
    });
    update(); if (!('ontouchstart' in window)) ta.focus();
  }

  /* ---- Photo viewer ---- */
  const lb = $('#lightbox');
  document.addEventListener('click', e => {
    const im = e.target.closest('.js-lightbox');
    if (im && lb) { $('img', lb).src = im.src; lb.classList.remove('d-none'); }
    else if (lb && e.target.closest('#lightbox')) lb.classList.add('d-none');
  });

  /* ---- Esc: close the photo, otherwise leave the chat room for the conversations page (not while a draft is typed) ---- */
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (lb && !lb.classList.contains('d-none')) return lb.classList.add('d-none');
    if ($('.modal.show, .dropdown-menu.show')) return;
    if ($('#composeForm textarea')?.value.trim()) return;
    if (room && room.dataset.lobbyUrl) location.href = room.dataset.lobbyUrl;
  });
})();