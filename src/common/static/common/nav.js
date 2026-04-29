/**
 * Mobile navigation: hamburger toggles the user menu panel and backdrop.
 * Closes on backdrop click, Escape, or when the viewport becomes desktop-wide.
 */
(function () {
  "use strict";

  const MOBILE_MQ = "(max-width: 767px)";

  function isMobileViewport() {
    return window.matchMedia(MOBILE_MQ).matches;
  }

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
      if (isMobileViewport()) {
        nav.setAttribute("aria-hidden", open ? "false" : "true");
      } else {
        nav.removeAttribute("aria-hidden");
      }
    }

    function close() {
      setOpen(false);
    }

    toggle.addEventListener("click", function () {
      if (!isMobileViewport()) {
        return;
      }
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

    window.matchMedia(MOBILE_MQ).addEventListener("change", function (ev) {
      if (!ev.matches) {
        close();
        nav.removeAttribute("aria-hidden");
      } else if (!nav.classList.contains("is-open")) {
        nav.setAttribute("aria-hidden", "true");
      }
    });

    if (isMobileViewport() && !nav.classList.contains("is-open")) {
      nav.setAttribute("aria-hidden", "true");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNav);
  } else {
    initNav();
  }
})();
