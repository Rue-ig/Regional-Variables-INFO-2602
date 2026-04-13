// PATH: app/static/js/events.js

(function () {
  const form = document.querySelector(".filter-bar");
  const keywordInput = document.querySelector('input[name="keyword"]');

  if (!form || !keywordInput)
    return;

  let debounceTimer;
  keywordInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => form.submit(), 400);
  });
})();

(function () {
  const SCROLL_KEY = "events_scroll";
  const form = document.querySelector(".filter-bar");

  if (!form)
    return;

  const saved = sessionStorage.getItem(SCROLL_KEY);

  if (saved) {
    window.scrollTo(0, parseInt(saved, 10));
    sessionStorage.removeItem(SCROLL_KEY);
  }

  form.addEventListener("submit", () => {
    sessionStorage.setItem(SCROLL_KEY, String(window.scrollY));
  });
})();

(function () {
  const picker = document.getElementById("starPicker");

  if (!picker)
    return;

  const labels = picker.querySelectorAll("label");
  labels.forEach((label, idx) => {
    label.addEventListener("mouseover", () => {
      labels.forEach((l, i) => {
        l.querySelector(".star").style.color = i <= idx ? "#f59e0b" : "";
      });
    });
    label.addEventListener("mouseleave", () => {
      const checked = picker.querySelector("input:checked");
      const checkedIdx = checked ? parseInt(checked.value, 10) - 1 : -1;

      labels.forEach((l, i) => {
        l.querySelector(".star").style.color = i <= checkedIdx ? "#f59e0b" : "";
      });
    });
    
    label.querySelector("input").addEventListener("change", () => {
      labels.forEach((l, i) => {
        l.querySelector(".star").style.color = i <= idx ? "#f59e0b" : "";
      });
    });
  });
})();