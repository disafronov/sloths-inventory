/**
 * Navigation: hamburger toggles the user menu panel and backdrop.
 * Closes on backdrop click or Escape.
 */
(function () {
  "use strict";

  function initNav() {
    const toggle = document.querySelector("[data-nav-toggle]");
    const nav = document.querySelector("[data-site-nav]");
    const backdrop = document.querySelector("[data-nav-backdrop]");

    if (!toggle || !nav) {
      return;
    }

    /** @param {boolean} open */
    function setOpen(open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      nav.classList.toggle("is-open", open);
      toggle.classList.toggle("is-open", open);
      if (backdrop) {
        backdrop.hidden = !open;
      }
      document.body.classList.toggle("nav-open", open);
      nav.setAttribute("aria-hidden", open ? "false" : "true");
    }

    function close() {
      setOpen(false);
    }

    toggle.addEventListener("click", function () {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      setOpen(!expanded);
    });

    if (backdrop) {
      backdrop.addEventListener("click", close);
    }

    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && nav.classList.contains("is-open")) {
        close();
        toggle.focus();
      }
    });

    nav.setAttribute("aria-hidden", "true");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNav);
  } else {
    initNav();
  }
})();
