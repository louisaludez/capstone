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

document
  .getElementById("check-out-modal-btn")
  .addEventListener("click", function () {

    console.log("Checkout button clicked");
    checkoutOverlay.style.display = "flex";

  });

document.querySelector(".checkout-overlay").addEventListener("click", (e) => {
  if (!document.querySelector(".checkout-modal").contains(e.target)) {
    document.querySelector(".checkout-overlay").style.display = "none";
    closeCheckoutModal();
  }
});

pm.addEventListener("change", toggleCF);


// function startCheckOutTimer(duration, display) {
//   if (checkOutTimerInterval) {
//     clearInterval(checkOutTimerInterval);
//   }
//   let timer = duration - 1,
//     minutes,
//     seconds;
//   checkOutTimerInterval = setInterval(function () {
//     minutes = parseInt(timer / 60, 10);
//     seconds = parseInt(timer % 60, 10);
//     minutes = minutes < 1 ? "" + minutes : minutes;
//     seconds = seconds < 10 ? "0" + seconds : seconds;

//     display.textContent = `${minutes}:${seconds}`;
//     console.log(`Timer: ${minutes}:${seconds}`);
//     if (--timer < 0) {
//       timer = duration;
//       clearInterval(walkInTimerInterval);
//     }
//   }, 1000);
// }

function closeCheckoutModal() {
  checkoutOverlay.style.display = "none";
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
      console.log("checkin date", response.bookings[0].check_in_date);
      console.log("guest", response.num_of_adults);
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

      // Check if guest is walk-in and hide room charges if so
      const selectedOption = $(".guests-name-checkout option:selected");
      const bookingSource = selectedOption.attr('data-booking-source') || '';
      const isWalkin = selectedOption.attr('data-is-walkin');
      const roomChargesWrapper = document.querySelector('.checkout-room-charges-wrapper');

      console.log('[checkout.js] bookingSource:', bookingSource, 'isWalkin:', isWalkin);

      // Only hide room charges and additional charges if source is 'walkin'
      const additionalChargesWrapper = document.querySelector('.checkout-additional-charges-wrapper');

      if (bookingSource === 'walkin' && roomChargesWrapper) {
        roomChargesWrapper.style.display = 'none';
        roomChargesWrapper.style.visibility = 'hidden';
        roomChargesWrapper.style.height = '0';
        roomChargesWrapper.style.margin = '0';
        roomChargesWrapper.style.padding = '0';
        console.log('[checkout.js] Hiding Room Charges - guest is walk-in');
        $(".guest-billing-checkout").val(''); // Clear room charges value

        // Also hide Additional Charges for walk-in guests
        if (additionalChargesWrapper) {
          additionalChargesWrapper.style.display = 'none';
          additionalChargesWrapper.style.visibility = 'hidden';
          additionalChargesWrapper.style.height = '0';
          additionalChargesWrapper.style.margin = '0';
          additionalChargesWrapper.style.padding = '0';
          console.log('[checkout.js] Hiding Additional Charges - guest is walk-in');
          $(".guest-additional-charge-checkout").val(''); // Clear additional charges value
        }
      } else if (roomChargesWrapper) {
        roomChargesWrapper.style.display = 'flex';
        roomChargesWrapper.style.visibility = 'visible';
        roomChargesWrapper.style.height = '';
        roomChargesWrapper.style.margin = '';
        roomChargesWrapper.style.padding = '';
        console.log('[checkout.js] Showing Room Charges - guest is from reservation');
        $(".guest-billing-checkout").val(billing);

        // Also show Additional Charges for reservations
        if (additionalChargesWrapper) {
          additionalChargesWrapper.style.display = 'flex';
          additionalChargesWrapper.style.visibility = 'visible';
          additionalChargesWrapper.style.height = '';
          additionalChargesWrapper.style.margin = '';
          additionalChargesWrapper.style.padding = '';
          console.log('[checkout.js] Showing Additional Charges - guest is from reservation');
        }
      } else {
        $(".guest-billing-checkout").val(billing);
      }
      $(".guest-rm-billing-checkout").val(roomService);
      $(".guest-laundry-billing-checkout").val(laundry);
      $(".guest-cafe-billing-checkout").val(cafe);
      $(".guest-ep-billing-checkout").val(excessPax);

      // Only set additional charges if not walk-in
      if (bookingSource !== 'walkin') {
        $(".guest-additional-charge-checkout").val(additional);
      } else {
        $(".guest-additional-charge-checkout").val('');
      }

      // Calculate total - exclude billing (room charges) and additional charges if walk-in
      let total;
      if (bookingSource === 'walkin') {
        // For walk-in: only laundry and cafe (exclude room charges and additional charges)
        total = laundry + cafe;
        console.log('[checkout.js] Walk-in total (excluding room charges and additional charges):', total);
      } else {
        // For reservations or checkin: include all charges including room charges and additional charges
        total = billing + roomService + laundry + cafe + excessPax + additional;
        console.log('[checkout.js] Reservation/Checkin total (including room charges and additional charges):', total);
      }
      $(".guest-total-balance-checkout").val(total.toFixed(2));
    },
    error: function (message) {
      console.error("Error fetching guest data:", message);
    },
  });
});

$(".checkout-submit-btn").on("click", function () {

  console.log("Checkout button clicked");
  $.ajax({
    url: "/staff/api/checkout/",
    type: "POST",
    data: {
      csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),

      guest_id: $(".guests-name-checkout").val(),
      check_in: $(".guest-check-in-date-co").val(),
      check_out: $(".guest-check-out-date-co").val(),
      room: $(".guest-room-type-checkout").val(),

      // Billing Breakdown
      total_billing: $(".guest-billing-checkout").val(),
      room_service: $(".guest-rm-billing-checkout").val(),
      laundry: $(".guest-laundry-billing-checkout").val(),
      cafe: $(".guest-cafe-billing-checkout").val(),
      excess_pax: $(".guest-ep-billing-checkout").val(),
      additional_charges: $(".guest-additional-charge-checkout").val(),

      // Payment info
      payment_method: $(".checkout-payment-method").val(),
      card_number: $(".checkout-card-number").val(),
      card_expiry: $(".checkout-card-exp-date").val(),
      card_cvc: $(".checkout-card-cvc").val(),
      billing_address: $(".checkout-billing-address").val(),
      balance: $(".guest-total-balance-checkout").val(),
    },
    success: function (response) {
      Swal.fire({
        icon: "success",
        title: "Checkout Successful",
        text: response.message || "Guest has been checked out.",
      }).then(function () {
        window.location.reload();
      });
      closeCheckoutModal();


    },
    error: function (xhr) {
      Swal.fire({
        icon: "error",
        title: "Checkout Failed",
        text: xhr.responseText || "Something went wrong.",
      });
    },
  });
});