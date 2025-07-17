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


$(".guests-name-checkout").on("change", function () {
  console.log("Guest name changed");
  console.log($(this).val());
  var guest_id = $(this).val();
  $.ajax({
    url: `/staff/get-guest/${guest_id}/`,
    type: "GET",
    success: function (response) {
      console.log("Gusest data received:", response);
      console.log("Guest Email:", response.email);
      console.log("Guest Address:", response.address);
      console.log("checkin date",response.bookings[0].check_in_date )
      console.log("guest", response.num_of_adults)
      $(".guest-address-checkout").val(response.address);
      $(".guest-email-checkout").val(response.email);
      $(".guest-birth-checkout").val(response.date_of_birth);
       $(".guest-check-in-date-co").val(response.check_in_date);
      $(".guest-check-out-date-co").val(response.check_out_date);
      $(".guest-room-type-checkout").val(response.room);
      $(".total-guest-checkout").val(response.total_of_guests);
      $(".no-adults-checkout").val(response.num_of_adults);
      $(".no-children-checkout").val(response.num_of_children);
      $(".no-below-7-checkout").val(response.no_of_children_below_7);
      
      function toNumber(value) {
        return parseFloat(value) || 0;
      }

      let billing = toNumber(response.billing);
      let roomService = toNumber(response.room_service_billing);
      let laundry = toNumber(response.laundry_billing);
      let cafe = toNumber(response.cafe_billing);
      let excessPax = toNumber(response.excess_pax_billing);
      let additional = toNumber(response.additional_charge_billing);
      $(".guest-billing-checkout").val(billing);
      $(".guest-rm-billing-checkout").val(roomService);
      $(".guest-laundry-billing-checkout").val(laundry);
      $(".guest-cafe-billing-checkout").val(cafe);
      $(".guest-ep-billing-checkout").val(excessPax);
      $(".guest-additional-charge-checkout").val(additional);
      let total = billing + roomService + laundry + cafe + excessPax + additional;
      $(".guest-total-balance-checkout").val(total.toFixed(2));
    },
    error: function (message) {
      console.error("Error fetching guest data:", message);
    },
  });
});