"use strict";
// Native validation still works without JavaScript; Flask validates every write again.
document.querySelectorAll("[data-toggle-password]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.togglePassword);
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.textContent = show ? "Hide" : "Show";
    button.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
});
// Visible system status: a progress bar while the next page is requested.
function startLoading() {
  document.documentElement.classList.add("is-loading");
}
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href]");
  if (
    !link ||
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    link.target ||
    link.hasAttribute("download") ||
    link.origin !== location.origin ||
    (link.pathname === location.pathname && link.hash)
  )
    return;
  startLoading();
});
document.querySelectorAll(".flash-close").forEach((button) => {
  button.addEventListener("click", () => button.closest(".flash").remove());
});
// Filters apply as soon as a choice changes; the Apply button remains for keyboards and no-JS.
document.querySelectorAll("form[data-autosubmit]").forEach((form) => {
  form.querySelectorAll("select, input[type=checkbox]").forEach((control) => {
    control.addEventListener("change", () => form.requestSubmit());
  });
});
document.querySelectorAll("[data-fill-email]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById("email").value = button.dataset.fillEmail;
    document.getElementById("password").value = button.dataset.fillPassword;
    document.getElementById("password").focus();
  });
});
const confirmDialog = document.getElementById("confirm-dialog");
let awaitingForm = null;
let previouslyFocused = null;
let secondStep = false;
// Costly actions can ask twice: data-confirm-again holds the second question.
function showConfirmation(form, again) {
  const label = form.dataset.confirmLabel || "Confirm";
  confirmDialog.dataset.tone = form.dataset.tone || "";
  document.getElementById("dialog-title").textContent = again
    ? "Last check"
    : form.dataset.confirmTitle || "Are you sure?";
  document.getElementById("dialog-message").textContent = again
    ? form.dataset.confirmAgain
    : form.dataset.confirm;
  document.getElementById("dialog-confirm").textContent = again
    ? "Yes, " + label.replace(/^Yes, /, "").toLowerCase()
    : label;
  if (!confirmDialog.open) confirmDialog.showModal();
  document.getElementById("dialog-cancel").focus();
}
function closeConfirmation() {
  confirmDialog.close();
  if (previouslyFocused) previouslyFocused.focus();
}
document
  .getElementById("dialog-cancel")
  .addEventListener("click", closeConfirmation);
confirmDialog.addEventListener("close", () => {
  awaitingForm = null;
  secondStep = false;
});
document.getElementById("dialog-confirm").addEventListener("click", () => {
  const form = awaitingForm;
  if (!form) return;
  if (form.dataset.confirmAgain && !secondStep) {
    secondStep = true;
    showConfirmation(form, true);
    return;
  }
  confirmDialog.close();
  form.dataset.confirmed = "yes";
  form.requestSubmit();
});
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const password = form.querySelector('[name="password"]');
    const confirmation = form.querySelector('[name="confirm_password"]');
    if (password && confirmation) {
      confirmation.setCustomValidity(
        password.value === confirmation.value
          ? ""
          : "Your passwords do not match.",
      );
    }
    if (!form.reportValidity()) {
      form.classList.add("was-validated");
      event.preventDefault();
      return;
    }
    if (form.dataset.confirm && form.dataset.confirmed !== "yes") {
      event.preventDefault();
      awaitingForm = form;
      previouslyFocused = document.activeElement;
      showConfirmation(form, false);
      return;
    }
    if ((form.getAttribute("method") || "get").toLowerCase() === "post") {
      if (form.dataset.submitting) {
        event.preventDefault();
        return;
      }
      form.dataset.submitting = "yes";
      const button =
        event.submitter ||
        form.querySelector('button[type="submit"],button:not([type])');
      if (button) {
        button.dataset.originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = button.dataset.processing || "Saving…";
      }
      form.setAttribute("aria-busy", "true");
    }
    startLoading();
  });
  form
    .querySelectorAll('[name="password"],[name="confirm_password"]')
    .forEach((input) => {
      input.addEventListener("input", () => {
        const confirmation = form.querySelector('[name="confirm_password"]');
        if (confirmation) confirmation.setCustomValidity("");
      });
    });
});
// Back/Forward can restore a page built for a different sign-in state (the
// log-in page after signing in, or private pages after logging out). When the
// state no longer matches, load the page again so the server decides what to show.
function signedInNow() {
  return document.cookie.split("; ").includes("cg_signed_in=1");
}
function matchSignInState() {
  const rendered = document.body.dataset.signedIn === "1";
  if (rendered !== signedInNow()) {
    location.replace(location.pathname + location.search);
  }
}
window.addEventListener("pageshow", matchSignInState);
window.addEventListener("pageshow", () => {
  document.documentElement.classList.remove("is-loading");
  document.querySelectorAll("form[data-submitting]").forEach((form) => {
    delete form.dataset.submitting;
    form.removeAttribute("aria-busy");
    form.querySelectorAll("button:disabled").forEach((button) => {
      button.disabled = false;
      button.textContent = button.dataset.originalLabel || "Submit";
    });
  });
});
document.querySelectorAll('[name="preset"]').forEach((input) => {
  input.addEventListener("change", () => {
    const amount = document.getElementById("donation-amount");
    amount.value = input.value === "custom" ? "" : input.value;
    if (input.value === "custom") amount.focus();
  });
});
const goal = document.querySelector('input[name="goal"]');
if (goal) {
  goal.min = "1";
  goal.max = "10000000";
  goal.step = "0.01";
}
const slots = document.querySelector('input[name="slots"]');
if (slots) {
  slots.min = "1";
  slots.max = "10000";
  slots.step = "1";
}
const volunteerCheckbox = document.getElementById("enable-volunteers");
if (volunteerCheckbox) {
  const fields = document.querySelectorAll(
    "#volunteer-options input,#volunteer-options textarea",
  );
  const update = () => {
    document.getElementById("volunteer-options").hidden =
      !volunteerCheckbox.checked;
    fields.forEach((field) => {
      field.required = volunteerCheckbox.checked;
    });
  };
  volunteerCheckbox.addEventListener("change", update);
  update();
}
document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener("change", () => {
    const file = input.files[0];
    const max = input.accept === ".pdf" ? 10 : 3;
    const message =
      file && file.size > max * 1024 * 1024
        ? `Choose a file no larger than ${max} MB.`
        : "";
    input.setCustomValidity(message);
    input.closest(".field").querySelector(".file-feedback").textContent =
      message || (file ? file.name : "");
    if (message) input.reportValidity();
  });
});
