(function () {
  var home = new URL("index.html", document.baseURI).href;
  document
    .querySelectorAll("a.doc-header__brand, a.doc-back, .site-header a.brand")
    .forEach(function (el) {
      el.setAttribute("href", home);
    });
})();
