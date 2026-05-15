(function () {
  const desktopQuery = window.matchMedia("(min-width: 768px)");
  const AUTO_MS = 3000;
  const TRANSITION = "transform 0.5s cubic-bezier(0.42, 0, 0.58, 1)";
  const GAP = 19;
  const VIEW_W_PER_H = 968 / 600;
  const COPIES = 3;
  /** Старт: в окне слайды 6 — 1 — 2 (индексы ленты 5,6,7 при порядке 1…6 × копии) */
  const P_BASE = 5;

  const DEFAULT_SLIDES = [
    { src: "assets/slides/img01.png", alt: "Удобно добавлять", loading: "eager" },
    { src: "assets/slides/img02.png", alt: "И изменять заметки", loading: "lazy" },
    { src: "assets/slides/img03.png", alt: "Учитывайте не только ТО", loading: "lazy" },
    { src: "assets/slides/img04.png", alt: "", loading: "lazy" },
    { src: "assets/slides/img05.png", alt: "", loading: "lazy" },
    { src: "assets/slides/img06.png", alt: "", loading: "lazy" },
  ];

  function protectImages(root) {
    if (!root) return;
    root.querySelectorAll("img").forEach(function (img) {
      img.setAttribute("draggable", "false");
      img.addEventListener("dragstart", function (e) {
        e.preventDefault();
      });
      img.addEventListener("contextmenu", function (e) {
        e.preventDefault();
      });
    });
  }

  const mobileSlider = document.querySelector(".hero-slider--mobile");
  protectImages(mobileSlider);

  if (mobileSlider) {
    mobileSlider.addEventListener("dragstart", function (e) {
      e.preventDefault();
    });
  }

  if (mobileSlider && !desktopQuery.matches) {
    let isDragging = false;
    let startX = 0;
    let startScrollLeft = 0;
    let moved = false;

    mobileSlider.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      isDragging = true;
      moved = false;
      startX = e.pageX;
      startScrollLeft = mobileSlider.scrollLeft;
      mobileSlider.classList.add("is-dragging");
      mobileSlider.style.scrollSnapType = "none";
      mobileSlider.style.scrollBehavior = "auto";
    });

    window.addEventListener("mousemove", function (e) {
      if (!isDragging) return;
      const delta = e.pageX - startX;
      if (Math.abs(delta) > 3) moved = true;
      e.preventDefault();
      mobileSlider.scrollLeft = startScrollLeft - delta;
    });

    function endDrag() {
      if (!isDragging) return;
      isDragging = false;
      mobileSlider.classList.remove("is-dragging");
      mobileSlider.style.scrollSnapType = "";
      mobileSlider.style.scrollBehavior = "";
    }

    window.addEventListener("mouseup", endDrag);
    mobileSlider.addEventListener("mouseleave", endDrag);

    mobileSlider.addEventListener("click", function (e) {
      if (moved) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  }

  const carousel = document.querySelector("[data-carousel]");
  const track = document.querySelector("[data-carousel-track]");
  const btnPrev = document.querySelector(".hero-carousel__arrow--prev");
  const btnNext = document.querySelector(".hero-carousel__arrow--next");

  if (!carousel || !track) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function collectSlides() {
    if (mobileSlider) {
      const els = mobileSlider.querySelectorAll(".hero-slider__item");
      const out = Array.from(els).map(function (el) {
        const img = el.querySelector("img");
        return {
          src: img ? img.getAttribute("src") : "",
          alt: img ? img.getAttribute("alt") || "" : "",
          loading: img ? img.getAttribute("loading") || "lazy" : "lazy",
        };
      });
      if (out.length && out[0].src) return out;
    }
    return DEFAULT_SLIDES;
  }

  function buildDesktopTrack(slides) {
    track.innerHTML = "";
    const n = slides.length;
    if (n === 0) return;

    for (let c = 0; c < COPIES; c++) {
      for (let i = 0; i < n; i++) {
        const s = slides[i];
        const wrap = document.createElement("div");
        wrap.className = "hero-carousel__item";
        const img = document.createElement("img");
        img.src = s.src;
        img.alt = s.alt;
        img.loading = c === 0 && i === 0 ? "eager" : s.loading;
        img.draggable = false;
        wrap.appendChild(img);
        track.appendChild(wrap);
      }
    }
  }

  let centerIndex = 0;
  let p = P_BASE;
  let timerId = null;
  let items = [];
  let slideCount = 6;

  function syncP() {
    p = P_BASE + centerIndex;
  }

  function applyTransform(animate) {
    if (!items.length || p < 0 || p >= items.length) return;
    const el = items[p];
    if (!el) return;
    const x = el.offsetLeft;
    if (!animate || reducedMotion.matches) {
      track.style.transition = "none";
    } else {
      track.style.transition = TRANSITION;
    }
    track.style.transform = "translate3d(" + -x + "px,0,0)";
    if (!animate || reducedMotion.matches) {
      void track.offsetHeight;
      track.style.transition = TRANSITION;
    }
  }

  function layoutCarouselViewport() {
    const vp = document.querySelector(".hero-carousel__viewport");
    if (!vp || !desktopQuery.matches) return;
    const h = vp.clientHeight;
    if (h <= 0) return;

    let vpW = h * VIEW_W_PER_H;
    const maxW = window.innerWidth - 48 * 2 - 32 * 2 - 40;
    vpW = Math.max(200, Math.min(vpW, maxW));
    vp.style.width = Math.round(vpW) + "px";

    const slideW = (vpW - 2 * GAP) / 3;
    items.forEach(function (el) {
      el.style.flexShrink = "0";
      el.style.flexBasis = slideW + "px";
      el.style.width = slideW + "px";
    });
    applyTransform(false);
  }

  function restartTimer() {
    if (reducedMotion.matches) return;
    if (timerId) clearInterval(timerId);
    timerId = window.setInterval(goNext, AUTO_MS);
  }

  function goNext() {
    if (centerIndex < slideCount - 1) {
      centerIndex++;
      syncP();
      applyTransform(true);
    } else {
      centerIndex = 0;
      p = P_BASE + slideCount;
      if (reducedMotion.matches) {
        p = P_BASE;
        applyTransform(false);
      } else {
        applyTransform(true);
        function onEnd(e) {
          if (e.propertyName !== "transform") return;
          track.removeEventListener("transitionend", onEnd);
          p = P_BASE;
          applyTransform(false);
        }
        track.addEventListener("transitionend", onEnd);
      }
    }
  }

  function goPrev() {
    if (centerIndex > 0) {
      centerIndex--;
      syncP();
      applyTransform(true);
    } else {
      centerIndex = slideCount - 1;
      p = P_BASE + centerIndex;
      applyTransform(false);
    }
  }

  function initCarousel() {
    if (!desktopQuery.matches) {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
      }
      return;
    }

    const slides = collectSlides();
    slideCount = slides.length || 6;
    buildDesktopTrack(slides);
    protectImages(carousel);

    items = Array.from(track.querySelectorAll(".hero-carousel__item"));
    if (items.length === 0) return;

    centerIndex = 0;
    syncP();

    window.requestAnimationFrame(function () {
      layoutCarouselViewport();
    });

    if (timerId) clearInterval(timerId);
    if (!reducedMotion.matches) {
      timerId = window.setInterval(goNext, AUTO_MS);
    }

    if (btnNext) {
      btnNext.onclick = function () {
        goNext();
        restartTimer();
      };
    }
    if (btnPrev) {
      btnPrev.onclick = function () {
        goPrev();
        restartTimer();
      };
    }
  }

  function onResize() {
    if (!desktopQuery.matches) return;
    items = Array.from(track.querySelectorAll(".hero-carousel__item"));
    if (items.length) layoutCarouselViewport();
  }

  function boot() {
    if (desktopQuery.matches) initCarousel();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  desktopQuery.addEventListener("change", function () {
    if (desktopQuery.matches) {
      initCarousel();
    } else {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
      }
    }
    onResize();
  });

  window.addEventListener("resize", function () {
    window.requestAnimationFrame(onResize);
  });

  window.addEventListener("load", function () {
    window.requestAnimationFrame(onResize);
  });

  var heroSlide = document.querySelector(".hero-slide");
  if (heroSlide && typeof ResizeObserver !== "undefined") {
    var ro = new ResizeObserver(function () {
      window.requestAnimationFrame(onResize);
    });
    ro.observe(heroSlide);
  }
})();
