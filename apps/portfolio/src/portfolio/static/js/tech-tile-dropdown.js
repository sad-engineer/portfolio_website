/* Кликабельные выпадающие описания для иконок секций профессии. */
(function () {
  var dropdowns = Array.prototype.slice.call(document.querySelectorAll(".tech-tile-dropdown"));
  if (!dropdowns.length) return;

  var contentBoundsHost = document.querySelector(".page-content.page-profession") || document.querySelector(".page-content");
  if (!contentBoundsHost) return;

  var closeOthers = function (activeDropdown) {
    dropdowns.forEach(function (dropdown) {
      if (dropdown !== activeDropdown) {
        dropdown.open = false;
      }
    });
  };

  var positionMenu = function (dropdown) {
    var trigger = dropdown.querySelector(".tech-tile-dropdown__trigger");
    var menu = dropdown.querySelector(".tech-tile-dropdown__menu");
    if (!menu || !trigger) return;

    var contentRect = contentBoundsHost.getBoundingClientRect();
    var triggerRect = trigger.getBoundingClientRect();
    var maxWidth = Math.floor(contentRect.width / 2);
    var resolvedMaxWidth = Math.max(180, maxWidth);
    menu.style.setProperty("--tech-dropdown-max-width", resolvedMaxWidth + "px");
    menu.style.setProperty("--tech-dropdown-min-width", "260px");
    var baseTop = Math.floor(triggerRect.bottom + 6);
    var availableHeight = Math.floor(contentRect.bottom - baseTop - 4);
    menu.style.setProperty("--tech-dropdown-max-height", Math.max(120, availableHeight) + "px");
    menu.style.top = baseTop + "px";
    menu.style.left = Math.floor(triggerRect.left) + "px";

    menu.style.maxWidth = "none";
    menu.style.width = "max-content";
    var naturalWidth = Math.ceil(menu.getBoundingClientRect().width);

    if (naturalWidth <= resolvedMaxWidth) {
      menu.style.width = naturalWidth + "px";
      menu.style.maxWidth = resolvedMaxWidth + "px";
    } else {
      menu.style.width = resolvedMaxWidth + "px";
      menu.style.maxWidth = resolvedMaxWidth + "px";
    }

    var menuRect = menu.getBoundingClientRect();

    var clampedLeft = menuRect.left;
    if (menuRect.right > contentRect.right) {
      clampedLeft -= (menuRect.right - contentRect.right);
    }
    if (clampedLeft < contentRect.left) {
      clampedLeft = contentRect.left;
    }
    menu.style.left = Math.floor(clampedLeft) + "px";
  };

  var lastPointerX = 0;
  var lastPointerY = 0;

  var pointInRect = function (x, y, r) {
    return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
  };

  /* Триггер, зазор до fixed-панели и сама панель — иначе при движении к панели срабатывал бы «выход». */
  var isPointerInsideDropdown = function (dropdown, x, y) {
    if (!dropdown.open) return false;
    var trigger = dropdown.querySelector(".tech-tile-dropdown__trigger");
    var menu = dropdown.querySelector(".tech-tile-dropdown__menu");
    if (!trigger || !menu) return false;
    var tr = trigger.getBoundingClientRect();
    var mr = menu.getBoundingClientRect();
    if (pointInRect(x, y, tr) || pointInRect(x, y, mr)) return true;
    var gapTop = tr.bottom;
    var gapBottom = mr.top;
    if (gapBottom > gapTop) {
      var gx0 = Math.min(tr.left, mr.left);
      var gx1 = Math.max(tr.right, mr.right);
      if (x >= gx0 && x <= gx1 && y >= gapTop && y <= gapBottom) return true;
    }
    return false;
  };

  var closeIfPointerOutsideAll = function (x, y) {
    if (!dropdowns.some(function (d) {
      return d.open;
    })) {
      return;
    }
    if (dropdowns.some(function (d) {
      return isPointerInsideDropdown(d, x, y);
    })) {
      return;
    }
    dropdowns.forEach(function (d) {
      d.open = false;
    });
  };

  var rememberPointer = function (e) {
    lastPointerX = e.clientX;
    lastPointerY = e.clientY;
  };

  document.addEventListener("pointerdown", rememberPointer, true);

  document.addEventListener("pointermove", function (e) {
    rememberPointer(e);
    closeIfPointerOutsideAll(lastPointerX, lastPointerY);
  });

  /* scroll не всплывает: capture на document ловит и страницу, и overflow у потомков. */
  document.addEventListener(
    "scroll",
    function (e) {
      if (e.target && e.target.closest && e.target.closest(".tech-tile-dropdown__menu")) {
        return;
      }
      dropdowns.forEach(function (d) {
        d.open = false;
      });
    },
    true
  );

  dropdowns.forEach(function (dropdown) {
    dropdown.addEventListener("toggle", function () {
      if (!dropdown.open) return;
      closeOthers(dropdown);
      // После открытия details дождемся рендера и точно вычислим размеры панели.
      requestAnimationFrame(function () {
        positionMenu(dropdown);
      });
    });
  });

  document.addEventListener("click", function (event) {
    var clickedInside = event.target.closest(".tech-tile-dropdown");
    if (clickedInside) return;
    dropdowns.forEach(function (dropdown) {
      dropdown.open = false;
    });
  });

  window.addEventListener("resize", function () {
    dropdowns.forEach(function (dropdown) {
      if (dropdown.open) {
        positionMenu(dropdown);
      }
    });
  });
})();
