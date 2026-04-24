(function initProfessionWorkExperience() {
  const workBlocks = document.querySelectorAll("[data-work-experience]");
  if (!workBlocks.length) {
    return;
  }

  workBlocks.forEach((block) => {
    const slides = Array.from(block.querySelectorAll("[data-work-slide]"));
    const prevButton = block.querySelector("[data-work-prev]");
    const nextButton = block.querySelector("[data-work-next]");
    const counter = block.querySelector("[data-work-counter]");
    const bannerButtons = Array.from(block.querySelectorAll("[data-scroll-banner]"));

    if (!slides.length || !prevButton || !nextButton || !counter) {
      return;
    }

    let activeIndex = 0;
    const total = slides.length;
    const formatCounterPart = (value) => String(value).padStart(2, "0");

    const render = () => {
      slides.forEach((slide, idx) => {
        slide.classList.toggle("is-active", idx === activeIndex);
      });
      counter.textContent = `${formatCounterPart(activeIndex + 1)} — ${formatCounterPart(total)}`;
      prevButton.disabled = activeIndex === 0;
      nextButton.disabled = activeIndex === total - 1;
    };

    prevButton.addEventListener("click", () => {
      if (activeIndex === 0) {
        return;
      }
      activeIndex -= 1;
      render();
    });

    nextButton.addEventListener("click", () => {
      if (activeIndex >= total - 1) {
        return;
      }
      activeIndex += 1;
      render();
    });

    counter.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        if (event.deltaY > 0) {
          if (activeIndex >= total - 1) {
            return;
          }
          activeIndex += 1;
        } else if (event.deltaY < 0) {
          if (activeIndex === 0) {
            return;
          }
          activeIndex -= 1;
        } else {
          return;
        }
        render();
      },
      { passive: false },
    );

    bannerButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const infoBanner =
          document.getElementById("info-banner-section") || document.querySelector(".info-banner");
        if (!infoBanner) {
          return;
        }
        infoBanner.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });

    render();
  });
})();
