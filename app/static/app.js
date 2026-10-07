const params = new URLSearchParams(window.location.search);
const toast = document.getElementById("toast");

const messages = {
  created: "Listing published successfully.",
  claimed: "Verification request submitted privately.",
  updated: "Claim status updated.",
  resolved: "Listing marked resolved.",
  sent: "Message sent.",
  welcome: "Account created successfully."
};

for (const key of Object.keys(messages)) {
  if (params.get(key) === "1") {
    showToast(messages[key], "success");
    break;
  }
}

const errors = {
  own: "You cannot claim your own listing.",
  resolved: "This listing has already been resolved.",
  answer: "Please enter a valid verification answer.",
  duplicate: "You already submitted a claim for this item.",
  "claim-not-needed": "Lost listings do not use ownership claims.",
  message: "Message must contain 1–600 characters."
};

if (params.get("error") && errors[params.get("error")]) {
  showToast(errors[params.get("error")], "error");
}

function showToast(message, kind = "success") {
  if (!toast) return;
  toast.textContent = message;
  toast.className = "toast show " + kind;
  setTimeout(() => { toast.className = "toast"; }, 3500);
}

document.querySelectorAll(".submit-form").forEach(form => {
  form.addEventListener("submit", () => {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    button.dataset.original = button.textContent;
    button.textContent = "Please wait…";
    button.disabled = true;
  });
});
