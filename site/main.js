// Параллакс первого экрана: дом отстаёт от прокрутки, текст уходит быстрее,
// поэтому заголовок «проезжает» за фасадом.
(() => {
  const hero = document.querySelector(".hero");
  const layers = [...document.querySelectorAll("[data-speed]")];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  // телефон и вертикальный планшет: дом стоит в потоке между заголовком и текстом,
  // поэтому он не отстаёт, а наоборот подъезжает вверх и накрывает заголовок
  const stacked = matchMedia("(max-width: 760px), (max-width: 1180px) and (max-aspect-ratio: 1/1)");
  if (!hero || !layers.length) return;

  let queued = false;
  const update = () => {
    queued = false;
    const y = Math.min(scrollY, hero.offsetHeight);
    for (const el of layers) {
      const speed = stacked.matches ? el.dataset.speedStacked ?? 0 : el.dataset.speed;
      el.style.transform = `translate3d(0, ${(y * speed).toFixed(1)}px, 0)`;
    }
  };
  const onScroll = () => {
    if (reduce.matches || queued) return;
    queued = true;
    requestAnimationFrame(update);
  };

  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  update();
})();

// Каталог. На компьютере секция закреплена на экране, и прокрутка листает
// направления: новое фото въезжает поверх прошлого, как стеклянная створка.
// На телефоне и вертикальном планшете — обычная лента со свайпом.
(() => {
  const catalog = document.querySelector(".catalog");
  if (!catalog) return;
  const slides = [...catalog.querySelectorAll(".cat-slide")];
  const navLinks = [...catalog.querySelectorAll(".catalog__nav a")];
  const strip = catalog.querySelector(".catalog__slides");
  const count = catalog.querySelector(".catalog__count b");
  const bar = catalog.querySelector(".catalog__bar");
  const [prev, next] = catalog.querySelectorAll(".arrow");
  const stacked = matchMedia("(max-width: 760px), (max-width: 1180px) and (max-aspect-ratio: 1/1)");
  const n = slides.length;
  const DOOR_MS = 1100;
  let current = 0;
  const timers = new WeakMap();

  const mark = (i) => {
    count.textContent = i + 1;
    navLinks.forEach((a, k) => a.setAttribute("aria-current", k === i ? "true" : "false"));
    prev.disabled = i === 0;
    next.disabled = i === n - 1;
  };

  // смена направления на компьютере
  const show = (i) => {
    if (i === current) return;
    const from = slides[current];
    const to = slides[i];
    catalog.classList.toggle("is-back", i < current);
    slides.forEach((s) => {
      if (s !== from && s !== to) s.classList.remove("is-active", "is-entering", "is-leaving");
    });
    from.classList.remove("is-active", "is-entering");
    from.classList.add("is-leaving");
    to.classList.remove("is-leaving");
    to.classList.add("is-active", "is-entering");
    clearTimeout(timers.get(from));
    clearTimeout(timers.get(to));
    timers.set(from, setTimeout(() => from.classList.remove("is-leaving"), DOOR_MS));
    timers.set(to, setTimeout(() => to.classList.remove("is-entering"), DOOR_MS));
    current = i;
    mark(i);
  };

  // где на странице начинается i-е направление
  const scrollSpan = () => catalog.offsetHeight - innerHeight;
  const topOf = (i) => catalog.offsetTop + ((i + 0.35) / n) * scrollSpan();

  let queued = false;
  const onScroll = () => {
    if (queued || stacked.matches) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      const p = Math.min(1, Math.max(0, -catalog.getBoundingClientRect().top / scrollSpan()));
      bar.style.setProperty("--p", p.toFixed(4));
      show(Math.min(n - 1, Math.floor(p * n)));
    });
  };

  const go = (i) => {
    i = Math.max(0, Math.min(n - 1, i));
    if (stacked.matches) {
      strip.scrollTo({ left: slides[i].offsetLeft - strip.offsetLeft - parseFloat(getComputedStyle(strip).paddingLeft), behavior: "smooth" });
    } else {
      scrollTo({ top: topOf(i), behavior: "smooth" });
    }
  };

  prev.addEventListener("click", () => go(current - 1));
  next.addEventListener("click", () => go(current + 1));

  // ссылки вида #cat-dushevye (меню, полоса в первом экране)
  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href^="#cat-"]');
    if (!a) return;
    const i = slides.findIndex((s) => "#" + s.id === a.getAttribute("href"));
    if (i < 0) return;
    e.preventDefault();
    if (stacked.matches) catalog.scrollIntoView({ behavior: "smooth" });
    go(i);
  });

  // лента на телефоне: счётчик по ближайшей карточке
  strip.addEventListener("scroll", () => {
    if (!stacked.matches) return;
    const x = strip.scrollLeft;
    let best = 0;
    slides.forEach((s, k) => {
      if (Math.abs(s.offsetLeft - strip.offsetLeft - x) < Math.abs(slides[best].offsetLeft - strip.offsetLeft - x)) best = k;
    });
    current = best;
    mark(best);
  }, { passive: true });

  // переход между раскладками: в ленте видны все карточки
  const reset = () => {
    slides.forEach((s, k) => {
      s.classList.remove("is-entering", "is-leaving");
      s.classList.toggle("is-active", k === current);
    });
    onScroll();
  };
  stacked.addEventListener("change", reset);

  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  mark(0);
  onScroll();
})();

// Работы: фильтр по направлениям, «Показать ещё» и просмотр фото на весь экран.
(() => {
  const section = document.querySelector(".works");
  if (!section) return;
  const tiles = [...section.querySelectorAll(".work")];
  const chips = [...section.querySelectorAll(".chip")];
  const more = section.querySelector(".works__more");
  let filter = "all";
  let expanded = false;

  const render = (animate = true) => {
    let shown = 0;
    tiles.forEach((t) => {
      const match = filter === "all" || t.dataset.cat === filter;
      const visible = match && (filter !== "all" || expanded || !t.hasAttribute("data-more"));
      t.hidden = !visible;
      t.classList.remove("is-in");
      if (visible && animate) {
        t.style.setProperty("--i", shown);
        void t.offsetWidth; // перезапуск анимации появления
        t.classList.add("is-in");
      }
      if (visible) shown++;
    });
    more.hidden = filter !== "all" || expanded;
    chips.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.filter === filter)));
  };

  const setFilter = (f) => { filter = f; render(); };
  chips.forEach((c) => c.addEventListener("click", () => setFilter(c.dataset.filter)));
  more.addEventListener("click", () => { expanded = true; render(); });

  // «Смотреть работы» в каталоге открывает нужный фильтр
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-works]");
    if (!a) return;
    e.preventDefault();
    setFilter(a.dataset.works);
    section.scrollIntoView({ behavior: "smooth" });
  });

  // просмотр на весь экран
  const viewer = document.createElement("dialog");
  viewer.className = "viewer";
  viewer.setAttribute("aria-label", "Просмотр фото");
  const icon = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg>`;
  viewer.innerHTML = `
    <span class="viewer__count" aria-live="polite"></span>
    <img alt="">
    <button class="viewer__btn viewer__prev" type="button" aria-label="Предыдущее фото">${icon("M15 5l-7 7 7 7")}</button>
    <button class="viewer__btn viewer__next" type="button" aria-label="Следующее фото">${icon("M9 5l7 7-7 7")}</button>
    <button class="viewer__btn viewer__close" type="button" aria-label="Закрыть">${icon("M6 6l12 12M18 6L6 18")}</button>`;
  document.body.append(viewer);
  const img = viewer.querySelector("img");
  const counter = viewer.querySelector(".viewer__count");
  let list = [];
  let at = 0;

  const showAt = (i) => {
    at = (i + list.length) % list.length;
    const a = list[at].querySelector("a");
    img.src = a.getAttribute("href");
    img.width = a.dataset.w;
    img.height = a.dataset.h;
    img.alt = a.querySelector("img").alt;
    counter.textContent = `${at + 1} / ${list.length}`;
  };

  section.addEventListener("click", (e) => {
    const a = e.target.closest(".work a");
    if (!a) return;
    e.preventDefault();
    list = tiles.filter((t) => !t.hidden);
    showAt(list.indexOf(a.parentElement));
    viewer.showModal();
  });
  viewer.querySelector(".viewer__prev").addEventListener("click", () => showAt(at - 1));
  viewer.querySelector(".viewer__next").addEventListener("click", () => showAt(at + 1));
  viewer.querySelector(".viewer__close").addEventListener("click", () => viewer.close());
  viewer.addEventListener("click", (e) => { if (e.target === viewer) viewer.close(); });
  viewer.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") showAt(at - 1);
    if (e.key === "ArrowRight") showAt(at + 1);
  });
  // свайп на телефоне
  let x0 = null;
  viewer.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  viewer.addEventListener("touchend", (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) showAt(at + (dx < 0 ? 1 : -1));
    x0 = null;
  });

  render(false);
})();

// Факты о компании: размерные линии прорисовываются, когда блок попадает в экран.
(() => {
  const facts = document.querySelector(".facts");
  if (!facts || !("IntersectionObserver" in window)) { facts?.classList.add("is-seen"); return; }
  const io = new IntersectionObserver(([e]) => {
    if (e.isIntersecting) { facts.classList.add("is-seen"); io.disconnect(); }
  }, { threshold: 0.4 });
  io.observe(facts);
})();

// Заявка. Сервера у сайта нет, поэтому пока заявка уходит письмом:
// открываем почту с готовым текстом. Отправку в Telegram подключим отдельно.
(() => {
  const form = document.querySelector(".request__form");
  if (!form) return;
  const note = form.querySelector(".request__note");
  const phone = form.elements.phone;
  const initial = note.innerHTML;

  phone.addEventListener("input", () => {
    phone.removeAttribute("aria-invalid");
    note.className = "request__note";
    note.innerHTML = initial;
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const digits = phone.value.replace(/\D/g, "");
    if (digits.length < 10) {
      phone.setAttribute("aria-invalid", "true");
      note.className = "request__note is-error";
      note.textContent = "Укажите телефон, чтобы мы могли перезвонить.";
      phone.focus();
      return;
    }
    const f = form.elements;
    const body = [
      "Телефон: " + f.phone.value.trim(),
      f.name.value.trim() && "Имя: " + f.name.value.trim(),
      "Что нужно: " + f.what.value,
      f.comment.value.trim() && "Подробности: " + f.comment.value.trim(),
    ].filter(Boolean).join("\n");
    location.href = "mailto:steklotlt@mail.ru?subject=" + encodeURIComponent("Заявка с сайта") + "&body=" + encodeURIComponent(body);
    note.className = "request__note is-ok";
    note.innerHTML = 'Открылась почта с готовым письмом — осталось нажать «Отправить». Если не открылась, позвоните: <a href="tel:+79278913800">+7 927 891-38-00</a>.';
  });
})();
