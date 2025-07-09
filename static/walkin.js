flatpickr("#dob", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#checkout", { dateFormat: "Y-m-d", allowInput: true });

const paymentMethod = document.querySelector(".walkin-payment-method");
const cardFields = document.querySelector(".walkin-card-fields");

function toggleCardFields() {
  if (paymentMethod.value === "card") {
    cardFields.classList.remove("hidden");
    cardFields.style.height = cardFields.scrollHeight + "px";
  } else {
    cardFields.classList.add("hidden");
    cardFields.style.height = "0px";
  }
}

const walkinOverlay = document.querySelector(".walkin-overlay");
const walkinModal = document.querySelector(".walkin-modal");

walkinOverlay.addEventListener("click", function (e) {
  if (!walkinModal.contains(e.target)) {
    walkinOverlay.style.display = "none";
  }
});
paymentMethod.addEventListener("change", toggleCardFields);
