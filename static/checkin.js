flatpickr("#ci-dob", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkout", { dateFormat: "Y-m-d", allowInput: true });

const ciPaymentMethod = document.querySelector(".checkin-payment-method");
const ciCardFields = document.querySelector(".checkin-card-fields");

function toggleCICardFields() {
  if (ciPaymentMethod.value === "card") {
    ciCardFields.classList.remove("hidden");
    ciCardFields.style.height = ciCardFields.scrollHeight + "px";
  } else {
    ciCardFields.classList.add("hidden");
    ciCardFields.style.height = "0px";
  }
}

ciPaymentMethod.addEventListener("change", toggleCICardFields);
const checkinOverlay = document.querySelector(".checkin-overlay");
const checkinModal = document.querySelector(".checkin-modal");

checkinOverlay.addEventListener("click", function (e) {
  if (!checkinModal.contains(e.target)) {
    checkinOverlay.style.display = "none";
  }
});

function startCheckInTimer(duration, display) {
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
    }
  }, 1000);
}
