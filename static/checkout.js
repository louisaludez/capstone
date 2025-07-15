flatpickr("#co-checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#co-checkout", { dateFormat: "Y-m-d", allowInput: true });

const pm = document.querySelector(".checkout-payment-method"),
  cf = document.querySelector(".checkout-card-fields");

function toggleCF() {
  if (pm.value === "card") {
    cf.classList.remove("hidden");
    cf.style.height = cf.scrollHeight + "px";
  } else {
    cf.classList.add("hidden");
    cf.style.height = "0px";
  }
}
const checkoutOverlay = document.querySelector(".checkout-overlay");
const checkoutModal = document.querySelector(".checkout-modal");
let timerDisplayCheckout = document.querySelector(".checkout-countdown-time");
let checkOutTimerInterval = null;
document
  .getElementById("check-out-modal-btn")
  .addEventListener("click", function () {
    var minutes = 5 * 60;
    console.log("Checkout button clicked");
    checkoutOverlay.style.display = "flex";
    timerDisplayCheckout.textContent = '5:00'
    startCheckOutTimer(minutes,timerDisplayCheckout)
   // Start the timer when the modal opens
  });

document.querySelector(".checkout-overlay").addEventListener("click", (e) => {
  if (!document.querySelector(".checkout-modal").contains(e.target)) {
    document.querySelector(".checkout-overlay").style.display = "none";
    closeCheckoutModal();
  }
});

pm.addEventListener("change", toggleCF);


function startCheckOutTimer(duration, display) {
  if (checkOutTimerInterval) {
    clearInterval(checkOutTimerInterval);
  }
  let timer = duration - 1,
    minutes,
    seconds;
  checkOutTimerInterval = setInterval(function () {
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

function closeCheckoutModal() {
  checkoutOverlay.style.display = "none";
 
  clearInterval(checkOutTimerInterval);
  checkOutTimerInterval = null;
}
