$(document).ready(function () {
  console.log("checkin.js loaded");
  function updateCheckinCardFields() {
    const paymentMethod = document.querySelector("#checkin #payment-method");
    const cardFields = document.querySelectorAll("#checkin .card-fields");
    if (paymentMethod.value === "credit-card") {
      cardFields.forEach((field) => {
        field.hidden = false;
      });
    } else {
      cardFields.forEach((field) => {
        field.hidden = true;
      });
    }
  }

  const logoURLCheckin = document.getElementById("checkin").dataset.logoUrl;
  var checkinModal = document.getElementById("checkin");
  var checkinBtn = document.getElementById("check-in-modal-btn");
  var checkinClose = document.getElementById("close-checkin-modal");
  let checkinTimerInterval = null;

  checkinBtn.onclick = function () {
    var fiveMinutes = 5 * 60,
      display = document.getElementById("checkin-timer");
    checkinModal.style.display = "block";

    startCheckinTimer(fiveMinutes, display);
    updateCheckinCardFields();
  };

  checkinClose.onclick = function () {
    checkinModal.style.display = "none";
    clearInterval(checkinTimerInterval);
    checkinTimerInterval = null;
  };

  window.onclick = function (event) {
    if (event.target === checkinModal) {
      checkinModal.style.display = "none";
      clearInterval(checkinTimerInterval);
      checkinTimerInterval = null;
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    const paymentMethod = document.querySelector("#checkin #payment-method");
    updateCheckinCardFields();
    paymentMethod.addEventListener("change", updateCheckinCardFields);
  });

  function startCheckinTimer(duration, display) {
    var timer = duration,
      minutes,
      seconds;
    checkinTimerInterval = setInterval(function () {
      minutes = parseInt(timer / 60, 10);
      seconds = parseInt(timer % 60, 10);
      minutes = minutes < 10 ? minutes : minutes;
      seconds = seconds < 10 ? "0" + seconds : seconds;

      display.textContent = minutes + ":" + seconds;
      console.log(display.textContent);
      if (--timer < 0) {
        timer = duration;
        clearInterval(checkinTimerInterval);
        checkinTimerInterval = null;
        checkinModal.style.display = "none";
        Swal.fire({
          title: `<h1 style="color:red;">Activity Failed</h1>`,
          text: "Please complete the check-in process.",
          showCloseButton: true,
          confirmButtonText: `<i class="fa fa-thumbs-up"></i> Close`,
          html: "<p>Time Remaining : 0:00 Minutes<br>Time Consumed : 5:00 Minutes</p>",
          icon: "error",
          customClass: {
            confirmButton: "my-confirm-btn-checkin",
          },
        });
      }
    }, 1000);
  }

  $("#checkin-room").on("click", function (event) {
    clearInterval(checkinTimerInterval);
    checkinTimerInterval = null;
    checkinModal.style.display = "none";
    guest_name = $(".guest-name-checkin").val();
    guest_address = $(".guest-address-checkin").val();
    guest_zip_code = $(".guest-zip_code-checkin").val();
    guest_birth = $(".guest-birth-checkin").val();
    guest_email = $(".guest-email-checkin").val();
    check_in = $(".check-in-i").val();
    check_out = $(".check-out-i").val();
    room = $(".room-type-checkin").val();
    total_guests = $(".total-guest-checkin").val();
    children = $(".NoOfChildren-checkin").val();
    adults = $(".adults-checkin").val();
    add_ons = $(".addOns-checkin").val();
    children_7_years = $(".children-checkin").val();
    payment_method = $(".payment-method-checkin").val();
    card_number = $(".card-number-checkin").val();
    exp_date = $(".exp-date-checkin").val();
    cvv = $(".cvv-checkin").val();
    billing_address = $(".billing-address-checkin").val();
    current_balance = $(".current-balance-checkin").val();
    $.ajax({
      type: "POST",
      url: "/staff/book-room/",
      data: {
        guest_name,
        guest_address,
        guest_zip_code,
        guest_birth,
        guest_email,
        check_in,
        check_out,
        room,
        total_guests,
        children,
        adults,
        add_ons,
        children_7_years,
        payment_method,
        card_number,
        exp_date,
        cvv,
        billing_address,
        current_balance,
        csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
      },

      success: function (response) {
        alert(response.message);
      },
    });
  });
});
