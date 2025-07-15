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
let timerDisplay = document.querySelector(".walkin-countdown-time");
let walkInTimerInterval = null;

document
  .getElementById("walk-in-modal-btn")
  .addEventListener("click", function () {
    var minutes = 5 * 60;
    console.log("Walk-in button clicked");
    walkinOverlay.style.display = "flex";
    startWalkInTimer(minutes, timerDisplay); // Start the timer when the modal opens
  });
walkinOverlay.addEventListener("click", function (e) {
  if (!walkinModal.contains(e.target)) {
    closeWalkinModal();
    console.log(
      "modal closed clicked outside the modal the time should stop now!"
    ); // Reset the interval variable
  }
});
paymentMethod.addEventListener("change", toggleCardFields);

function startWalkInTimer(duration, display) {
  if (walkInTimerInterval) {
    clearInterval(walkInTimerInterval);
  }
  var timer = duration - 1,
    minutes,
    seconds;
  walkInTimerInterval = setInterval(function () {
    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);
    minutes = minutes < 1 ? "" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    display.textContent = `${minutes}:${seconds}`;
    console.log(`Timer: ${minutes}:${seconds}`);
    if (--timer < 0) {
      timer = duration;
      clearInterval(walkInTimerInterval);

      // Hide the modal when the timer ends
    }
  }, 1000);
}

function closeWalkinModal() {
  walkinOverlay.style.display = "none";
  timerDisplay.textContent = "5:00";
  clearInterval(walkInTimerInterval);
  walkInTimerInterval = null;
}
