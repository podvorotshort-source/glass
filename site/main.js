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
