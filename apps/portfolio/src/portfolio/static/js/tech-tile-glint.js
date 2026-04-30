/* Групповой блик иконок на страницах профессий: размер группы зависит от числа видимых иконок. */
(function () {
  var pageRoot = document.querySelector(".page-content.page-profession");
  if (!pageRoot) {
    return;
  }

  var START_DELAY_MS = 2000;
  var LOOP_INTERVAL_MS = 2500;

  var readDelay = function (name, fallback) {
    var value = getComputedStyle(pageRoot).getPropertyValue(name).trim();
    if (!value) {
      return fallback;
    }
    var numeric = Number(value.replace("ms", "").trim());
    if (!Number.isNaN(numeric)) {
      return numeric;
    }
    return fallback;
  };

  var delayFirst = readDelay("--tech-glint-first-delay", 0);
  var delaySecond = readDelay("--tech-glint-second-delay", 140);
  var delayThird = readDelay("--tech-glint-third-delay", 280);
  var groupDelays = [delayFirst, delaySecond, delayThird];

  var getViewportLimits = function () {
    var header = document.querySelector(".site-header");
    var topLimit = 0;
    if (header) {
      var headerStyle = window.getComputedStyle(header);
      if (headerStyle.display !== "none" && headerStyle.visibility !== "hidden" && Number(headerStyle.opacity) !== 0) {
        var headerRect = header.getBoundingClientRect();
        if (headerRect.bottom > 0) {
          topLimit = Math.max(0, Math.min(window.innerHeight, headerRect.bottom));
        }
      }
    }
    return {
      top: topLimit,
      bottom: window.innerHeight,
      left: 0,
      right: window.innerWidth,
    };
  };

  var isVisibleTile = function (tile) {
    if (!tile || !tile.isConnected) {
      return false;
    }
    var style = window.getComputedStyle(tile);
    if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) {
      return false;
    }
    var rect = tile.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) {
      return false;
    }
    var viewport = getViewportLimits();
    return (
      rect.bottom > viewport.top &&
      rect.right > viewport.left &&
      rect.top < viewport.bottom &&
      rect.left < viewport.right
    );
  };

  var pickRandomTiles = function (tiles, count) {
    var copy = tiles.slice();
    for (var i = copy.length - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = copy[i];
      copy[i] = copy[j];
      copy[j] = tmp;
    }
    return copy.slice(0, count);
  };

  var getGroupSizeByVisibleCount = function (visibleCount) {
    if (visibleCount < 5) {
      return 1;
    }
    if (visibleCount <= 15) {
      return 2;
    }
    return 3;
  };

  var triggerGlint = function (tile, delayMs) {
    if (!tile) {
      return;
    }
    tile.classList.remove("is-glinting");
    // Форсируем reflow, чтобы повторный запуск анимации срабатывал стабильно.
    void tile.offsetWidth;
    tile.style.setProperty("--tech-glint-delay", String(delayMs) + "ms");
    tile.classList.add("is-glinting");
  };

  var runGroupGlint = function () {
    var allTiles = Array.prototype.slice.call(pageRoot.querySelectorAll(".tech-tile"));
    var visibleTiles = allTiles.filter(isVisibleTile);
    if (!visibleTiles.length) {
      return;
    }
    var groupSize = getGroupSizeByVisibleCount(visibleTiles.length);
    var selected = pickRandomTiles(visibleTiles, Math.min(groupSize, visibleTiles.length));
    selected.forEach(function (tile, index) {
      var delayMs = groupDelays[index] || 0;
      triggerGlint(tile, delayMs);
    });
  };

  document.addEventListener(
    "animationend",
    function (event) {
      var tile = event.target;
      if (!tile || !tile.classList || !tile.classList.contains("tech-tile")) {
        return;
      }
      tile.classList.remove("is-glinting");
      tile.style.removeProperty("--tech-glint-delay");
    },
    true
  );

  window.setTimeout(function () {
    runGroupGlint();
    window.setInterval(runGroupGlint, LOOP_INTERVAL_MS);
  }, START_DELAY_MS);
})();
