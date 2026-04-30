/**
 * Searchable select (vanilla JS).
 *
 * Motivation: Django admin uses a select widget with an in-dropdown search (select2).
 * For the user-facing UI we implement the same UX without adding build tooling.
 *
 * Usage:
 * - Add `data-searchable-select` to a <select>.
 * - Provide a placeholder via `data-search-placeholder` (optional).
 *
 * This script builds an accessible-ish combobox popup that syncs the underlying select value.
 */
(function () {
  "use strict";

  /** @param {HTMLSelectElement} select */
  function initSearchableSelect(select) {
    if (select.dataset.searchableSelectInit === "true") {
      return;
    }
    select.dataset.searchableSelectInit = "true";

    const placeholder =
      select.getAttribute("data-search-placeholder") || "Type to filter…";

    const wrapper = document.createElement("div");
    wrapper.className = "searchable-select";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "searchable-select__button";
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");

    const panel = document.createElement("div");
    panel.className = "searchable-select__panel";
    panel.hidden = true;

    const search = document.createElement("input");
    search.type = "search";
    search.className = "searchable-select__search";
    search.placeholder = placeholder;
    search.autocomplete = "off";
    search.setAttribute("inputmode", "search");

    const list = document.createElement("div");
    list.className = "searchable-select__list";
    list.setAttribute("role", "listbox");

    /** @type {{value: string, label: string, el: HTMLButtonElement}[]} */
    const items = [];

    function updateButtonLabel() {
      const opt = select.selectedOptions[0];
      button.textContent = opt ? opt.text : "";
    }

    function close() {
      panel.hidden = true;
      button.setAttribute("aria-expanded", "false");
    }

    function open() {
      panel.hidden = false;
      button.setAttribute("aria-expanded", "true");
      search.value = "";
      applyFilter("");
      // Delay focus to ensure the panel is visible.
      window.setTimeout(() => search.focus(), 0);
    }

    function toggle() {
      if (panel.hidden) {
        open();
      } else {
        close();
      }
    }

    function normalize(value) {
      return (value || "").toString().trim().toLowerCase();
    }

    /** @param {string} q */
    function applyFilter(q) {
      const n = normalize(q);
      for (const item of items) {
        const matches = n === "" || normalize(item.label).includes(n);
        item.el.hidden = !matches;
      }
    }

    function rebuild() {
      items.length = 0;
      list.innerHTML = "";

      for (const opt of Array.from(select.options)) {
        const optBtn = document.createElement("button");
        optBtn.type = "button";
        optBtn.className = "searchable-select__option";
        optBtn.textContent = opt.text;
        optBtn.setAttribute("role", "option");
        optBtn.dataset.value = opt.value;

        optBtn.addEventListener("click", () => {
          select.value = opt.value;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          updateButtonLabel();
          close();
          button.focus();
        });

        items.push({ value: opt.value, label: opt.text, el: optBtn });
        list.appendChild(optBtn);
      }

      updateButtonLabel();
    }

    button.addEventListener("click", toggle);
    search.addEventListener("input", () => applyFilter(search.value));

    document.addEventListener("click", (ev) => {
      if (!wrapper.contains(/** @type {Node} */ (ev.target))) {
        close();
      }
    });

    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !panel.hidden) {
        ev.preventDefault();
        close();
        button.focus();
      }
    });

    select.addEventListener("change", updateButtonLabel);

    // Build DOM.
    panel.appendChild(search);
    panel.appendChild(list);

    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(button);
    wrapper.appendChild(panel);
    wrapper.appendChild(select);

    // Keep the real select for POST, but hide it from sight.
    select.classList.add("searchable-select__native");

    rebuild();
  }

  function initAll() {
    /** @type {NodeListOf<HTMLSelectElement>} */
    const selects = document.querySelectorAll("select[data-searchable-select]");
    for (const select of selects) {
      initSearchableSelect(select);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
