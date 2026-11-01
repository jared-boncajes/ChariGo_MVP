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
const confirmDialog = document.getElementById("confirm-dialog");
let awaitingForm = null;
let previouslyFocused = null;
function closeConfirmation() {
  confirmDialog.close();
  if (previouslyFocused) previouslyFocused.focus();
  awaitingForm = null;
}
document
  .getElementById("dialog-cancel")
  .addEventListener("click", closeConfirmation);
confirmDialog.addEventListener("cancel", () => {
  awaitingForm = null;
});
document.getElementById("dialog-confirm").addEventListener("click", () => {
  const form = awaitingForm;
  confirmDialog.close();
  if (form) {
    form.dataset.confirmed = "yes";
    form.requestSubmit();
  }
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
      event.preventDefault();
      return;
    }
    if (form.dataset.confirm && form.dataset.confirmed !== "yes") {
      event.preventDefault();
      awaitingForm = form;
      previouslyFocused = document.activeElement;
      document.getElementById("dialog-message").textContent =
        form.dataset.confirm;
      confirmDialog.showModal();
      document.getElementById("dialog-cancel").focus();
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
window.addEventListener("pageshow", () => {
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
