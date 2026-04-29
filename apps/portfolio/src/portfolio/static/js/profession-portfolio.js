(function initProfessionPortfolio() {
  const portfolioBlocks = document.querySelectorAll("[data-portfolio]");
  if (!portfolioBlocks.length) {
    return;
  }

  const VISIBLE_RADIUS = 3; // Центр + 3 карточки слева и справа = 7 видимых.
  const FAST_MOTION_MS = 180; // Скорость анимации карточки при перемещении.
  const SLOW_MOTION_MS = 2000; // Скорость анимации карточки при перемещении.
  const AUTOPLAY_START_DELAY_MS = 2000; // Задержка перед повторным включением режима ожидания.

  const formatCounterPart = (value) => String(value).padStart(2, "0");

  const wrappedDelta = (index, activeIndex, total) => {
    let delta = index - activeIndex;
    if (delta > total / 2) {
      delta -= total;
    } else if (delta < -total / 2) {
      delta += total;
    }
    return delta;
  };

  const positionCard = (card, delta, trackWidth) => {
    const absDelta = Math.abs(delta);
    const sign = delta < 0 ? -1 : 1;
    const distanceByDepth = [0, trackWidth * 0.18, trackWidth * 0.3, trackWidth * 0.37];
    const rotateByDepth = [0, 45, 60, 75];
    const scaleByDepth = [1, 0.75, 0.65, 0.55];
    const depth = Math.min(absDelta, 3);
    const translateX = distanceByDepth[depth] * sign;
    const rotateY = rotateByDepth[depth] * -sign;
    const scale = scaleByDepth[depth];
    const translateY = 2 + depth * 2.5;
    const zIndex = 100 - depth;

    card.style.transform = `translate(-50%, -50%) translateX(${translateX}px) translateY(${translateY}%) rotateY(${rotateY}deg) scale(${scale})`;
    card.style.zIndex = String(zIndex);
    card.classList.remove("is-hidden");
    card.setAttribute("aria-hidden", "false");
  };

  portfolioBlocks.forEach((block) => {
    const cards = Array.from(block.querySelectorAll("[data-portfolio-card]"));
    const stage = block.querySelector("[data-portfolio-stage]");
    const counter = block.querySelector("[data-portfolio-counter]");
    const prevButton = block.querySelector("[data-portfolio-prev]");
    const nextButton = block.querySelector("[data-portfolio-next]");
    if (!cards.length || !counter || !stage) {
      return;
    }

    const total = cards.length;
    let activeIndex = 0;
    let autoplayIntervalId = null;
    let autoplayResumeTimeoutId = null;

    const render = (motionMs = FAST_MOTION_MS, easing = "ease-out") => {
      const trackWidth = stage.clientWidth;
      stage.style.setProperty("--motion-duration", `${motionMs}ms`);
      stage.style.setProperty("--motion-easing", easing);
      cards.forEach((card, idx) => {
        const delta = wrappedDelta(idx, activeIndex, total);
        if (Math.abs(delta) > VISIBLE_RADIUS) {
          card.classList.add("is-hidden");
          card.style.zIndex = "0";
          card.setAttribute("aria-hidden", "true");
          return;
        }
        positionCard(card, delta, trackWidth);
      });

      counter.textContent = `${formatCounterPart(activeIndex + 1)} — ${formatCounterPart(total)}`;
    };

    const moveNext = (motionMs = FAST_MOTION_MS, easing = "ease-out") => {
      activeIndex = (activeIndex + 1) % total;
      render(motionMs, easing);
    };

    const movePrev = (motionMs = FAST_MOTION_MS, easing = "ease-out") => {
      activeIndex = (activeIndex - 1 + total) % total;
      render(motionMs, easing);
    };

    const stopAutoplay = () => {
      if (autoplayIntervalId !== null) {
        clearInterval(autoplayIntervalId);
        autoplayIntervalId = null;
      }
      if (autoplayResumeTimeoutId !== null) {
        clearTimeout(autoplayResumeTimeoutId);
        autoplayResumeTimeoutId = null;
      }
    };

    const startAutoplay = () => {
      if (autoplayIntervalId !== null) {
        return;
      }
      autoplayIntervalId = setInterval(() => {
        moveNext(SLOW_MOTION_MS, "linear");
      }, 2000);
    };

    const scheduleAutoplayResume = () => {
      stopAutoplay();
      autoplayResumeTimeoutId = setTimeout(() => {
        autoplayResumeTimeoutId = null;
        startAutoplay();
      }, AUTOPLAY_START_DELAY_MS);
    };

    const handleWheelNavigation = (event) => {
      event.preventDefault();
      if (event.deltaY > 0) {
        moveNext(FAST_MOTION_MS, "ease-out");
      } else if (event.deltaY < 0) {
        movePrev(FAST_MOTION_MS, "ease-out");
      } else {
        return;
      }
      scheduleAutoplayResume();
    };

    if (prevButton) {
      prevButton.addEventListener("click", () => {
        movePrev(FAST_MOTION_MS, "ease-out");
        scheduleAutoplayResume();
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", () => {
        moveNext(FAST_MOTION_MS, "ease-out");
        scheduleAutoplayResume();
      });
    }

    counter.addEventListener("wheel", handleWheelNavigation, { passive: false });
    stage.addEventListener("wheel", handleWheelNavigation, { passive: false });

    stage.addEventListener("mouseenter", () => {
      stopAutoplay();
    });

    stage.addEventListener("mouseleave", () => {
      scheduleAutoplayResume();
    });

    render(FAST_MOTION_MS, "ease-out");
    startAutoplay();
  });
})();
