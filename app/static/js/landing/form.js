const MAX_UPLOAD_BYTES = 500 * 1024 * 1024;

function setError(field, message) {
  const input = document.getElementById(field);
  const error = document.getElementById(`${field}-error`);

  if (input) input.setAttribute("aria-invalid", message ? "true" : "false");
  if (error) error.textContent = message;
}

function clearErrors() {
  setError("youtube_url", "");
  setError("file", "");
}

export function initForm() {
  const form = document.getElementById("run-form");
  if (!form) return;

  const tabs = Array.from(form.querySelectorAll("[data-source-tab]"));
  const youtubePanel = document.getElementById("source-youtube");
  const uploadPanel = document.getElementById("source-upload");
  const youtubeInput = document.getElementById("youtube_url");
  const fileInput = document.getElementById("file");
  const submit = form.querySelector('button[type="submit"]');
  const submitLabel = submit ? submit.querySelector("[data-submit-label]") : null;
  const formError = document.querySelector(".form-error");

  let source = "youtube";

  function setSource(nextSource, focus) {
    source = nextSource;

    for (const tab of tabs) {
      const active = tab.dataset.sourceTab === source;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.tabIndex = active ? 0 : -1;
    }

    const isYoutube = source === "youtube";
    if (youtubePanel) youtubePanel.hidden = !isYoutube;
    if (uploadPanel) uploadPanel.hidden = isYoutube;
    if (youtubeInput) {
      youtubeInput.disabled = !isYoutube;
      youtubeInput.required = isYoutube;
    }
    if (fileInput) {
      fileInput.disabled = isYoutube;
      fileInput.required = !isYoutube;
    }

    clearErrors();

    if (focus) {
      const target = isYoutube ? youtubeInput : fileInput;
      if (target) target.focus({ preventScroll: true });
    }
  }

  for (const tab of tabs) {
    tab.addEventListener("click", () => setSource(tab.dataset.sourceTab, true));

    tab.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();

      const index = tabs.indexOf(tab);
      const direction = event.key === "ArrowRight" ? 1 : -1;
      const next = tabs[(index + direction + tabs.length) % tabs.length];
      setSource(next.dataset.sourceTab, false);
      next.focus();
    });
  }

  if (youtubeInput) {
    youtubeInput.addEventListener("input", () => setError("youtube_url", ""));
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => setError("file", ""));
  }

  form.addEventListener("submit", (event) => {
    clearErrors();

    if (source === "youtube") {
      const value = youtubeInput ? youtubeInput.value.trim() : "";

      if (!value) {
        event.preventDefault();
        setError("youtube_url", "Add a YouTube link or switch to Upload file.");
        if (youtubeInput) youtubeInput.focus();
        return;
      }

      try {
        const url = new URL(value);
        if (url.protocol !== "http:" && url.protocol !== "https:") {
          throw new Error("unsupported protocol");
        }
      } catch {
        event.preventDefault();
        setError("youtube_url", "Enter a valid http(s) YouTube link.");
        if (youtubeInput) youtubeInput.focus();
        return;
      }
    } else {
      const file = fileInput && fileInput.files ? fileInput.files[0] : null;

      if (!file) {
        event.preventDefault();
        setError("file", "Choose an audio or video file.");
        if (fileInput) fileInput.focus();
        return;
      }

      if (file.size > MAX_UPLOAD_BYTES) {
        event.preventDefault();
        setError("file", "The file is larger than the 500 MB limit.");
        if (fileInput) fileInput.focus();
        return;
      }
    }

    if (submit) {
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
    }
    if (submitLabel) {
      submitLabel.textContent = "STARTING…";
    }
    form.classList.add("is-submitting");
  });

  const missingYoutube = !youtubeInput || !youtubeInput.value.trim();
  setSource(formError && missingYoutube ? "upload" : "youtube", false);
}
