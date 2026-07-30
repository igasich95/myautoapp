(function () {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const AUTO_MS = 3000;
  const SWIPE_THRESHOLD = 40;

  // "\n" marks the explicit line break used in each caption (matches Figma).
  const SLIDES = [
    { src: "assets/slides/img01.png", caption: "Track mileage\nand expenses" },
    { src: "assets/slides/img02.png", caption: "Compare costs\nover time" },
    { src: "assets/slides/img03.png", caption: "Fuel tracking\nmade simple" },
    { src: "assets/slides/img04.png", caption: "Plan maintenance\nahead" },
    { src: "assets/slides/img05.png", caption: "Keep your\nmaintenance history" },
    { src: "assets/slides/img06.png", caption: "Get timely\nreminders" },
  ];

  function captionHTML(text) {
    return text
      .split("\n")
      .map(function (line) {
        return '<span class="slideshow__caption-line">' + line + "</span>";
      })
      .join("");
  }

  function captionText(text) {
    return text.replace(/\n/g, " ");
  }

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

  const slideshow = document.querySelector("[data-slideshow]");
  if (!slideshow) return;

  const capA = slideshow.querySelector("[data-cap-a]");
  const capB = slideshow.querySelector("[data-cap-b]");
  const photoA = slideshow.querySelector("[data-photo-a]");
  const photoB = slideshow.querySelector("[data-photo-b]");
  const dots = Array.from(slideshow.querySelectorAll(".slideshow__dot"));

  if (!capA || !capB || !photoA || !photoB) return;

  protectImages(slideshow);

  // Warm the cache so crossfades don't flash.
  SLIDES.forEach(function (s) {
    const im = new Image();
    im.src = s.src;
  });

  let index = 0;
  let activeIsA = true;
  let timerId = null;
  // Auto-advance runs whenever the tab is visible, but shuts off for good the
  // first time the visitor navigates by hand (dot or swipe) so it never yanks
  // the slide out from under someone who's reading it.
  let userPaused = false;

  function setDots(n) {
    dots.forEach(function (d, i) {
      d.classList.toggle("is-active", i === n);
      d.setAttribute("aria-selected", i === n ? "true" : "false");
    });
  }

  function goTo(n) {
    const len = SLIDES.length;
    n = ((n % len) + len) % len;
    if (n === index) return;

    const outCap = activeIsA ? capA : capB;
    const inCap = activeIsA ? capB : capA;
    const outPhoto = activeIsA ? photoA : photoB;
    const inPhoto = activeIsA ? photoB : photoA;

    inCap.innerHTML = captionHTML(SLIDES[n].caption);
    inPhoto.src = SLIDES[n].src;
    inPhoto.alt = captionText(SLIDES[n].caption);
    inCap.setAttribute("aria-hidden", "false");
    outCap.setAttribute("aria-hidden", "true");
    inPhoto.setAttribute("aria-hidden", "false");
    outPhoto.setAttribute("aria-hidden", "true");

    // Force reflow so the freshly-set src starts from opacity:0 before fading in.
    void inPhoto.offsetWidth;

    inCap.classList.add("is-active");
    inPhoto.classList.add("is-active");
    outCap.classList.remove("is-active");
    outPhoto.classList.remove("is-active");

    activeIsA = !activeIsA;
    index = n;
    setDots(index);
  }

  function next() {
    goTo(index + 1);
  }

  function prev() {
    goTo(index - 1);
  }

  function stopAuto() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  function startAuto() {
    stopAuto();
    if (userPaused || reducedMotion.matches || document.hidden) return;
    timerId = window.setInterval(next, AUTO_MS);
  }

  // Manual navigation disables auto-advance for the rest of the visit.
  function pauseAutoForGood() {
    userPaused = true;
    stopAuto();
  }

  dots.forEach(function (dot, i) {
    dot.addEventListener("click", function () {
      goTo(i);
      pauseAutoForGood(); // visitor took control — stop auto-advancing
    });
  });

  // Swipe to change slides (touch + mouse drag) — same crossfade animation.
  // touch-action: pan-y keeps vertical scrolling native; a horizontal drag
  // past the threshold switches slides.
  let startX = 0;
  let startY = 0;
  let swiping = false;

  slideshow.addEventListener("pointerdown", function (e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    if (e.target.closest(".slideshow__dot")) return; // let dots handle taps
    swiping = true;
    startX = e.clientX;
    startY = e.clientY;
  });

  window.addEventListener("pointerup", function (e) {
    if (!swiping) return;
    swiping = false;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (Math.abs(dx) > SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy) * 1.2) {
      if (dx < 0) next();
      else prev();
      pauseAutoForGood();
    }
  });

  window.addEventListener("pointercancel", function () {
    swiping = false;
  });

  // Pause when the tab is hidden.
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stopAuto();
    else startAuto();
  });

  reducedMotion.addEventListener("change", startAuto);

  startAuto();
})();
