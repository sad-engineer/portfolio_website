/* Логика запуска блика info-banner в зависимости от видимости в viewport. */
(function () {
  var banner = document.querySelector(".info-banner");
  if (!banner) return;

  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReducedMotion) return;

  var fullyVisible = function (element) {
    var rect = element.getBoundingClientRect();
    return rect.top >= 0 && rect.bottom <= window.innerHeight;
  };

  if (fullyVisible(banner)) {
    banner.classList.add("info-banner--glint-after-cards");
    return;
  }

  var observer = new IntersectionObserver(function (entries, obs) {
    var entry = entries[0];
    if (entry && entry.intersectionRatio >= 1) {
      banner.classList.add("info-banner--glint-on-visible");
      obs.disconnect();
    }
  }, { threshold: 1.0 });

  observer.observe(banner);
})();
