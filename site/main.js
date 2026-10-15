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
