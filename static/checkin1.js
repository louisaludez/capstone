$(document).ready(function () {
  console.log("checkin.js loaded");
  $(".payment-method-checkin").on("change", function () {
    const paymentMethod = $(this).val();
    const cardFields = $(".card-fields-checkin");
    if (paymentMethod === "credit-card") {
      console.log("Credit card selected");
      $(".card-fields.number").removeAttr("hidden");
      $(".card-fields").removeAttr("hidden");
    } else {
      console.log("Non-credit card selected");
      $(".card-fields.number").attr("hidden", true);
      $(".card-fields").attr("hidden", true);
      cardFields.hide(); // Hide the card fields
    }
  });
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
        Swal.fire({
          title: "Room Successfully Checked In!",
          text: "Your check-in has been completed.",
          html: `<p style="color:#1a2d1e">Guest: ${guest_name}<br>Room no. ${room}<br>Reference no. 00001</p>`,
          icon: "success",
          customClass: {
            confirmButton: "my-confirm-btn-checkin",
            denyButton: "my-deny-btn-checkin",
            title: "my-title-checkin",
            text: "my-text-checkin",
          },
          showDenyButton: true,
          confirmButtonText: "View Receipt",
          denyButtonText: "Activity Results",
        }).then((result) => {
          if (result.isConfirmed) {
            Swal.fire({
              title: "",
              showCloseButton: true,
              html: `
                <div style="font-family: Arial, sans-serif; text-align: center; font-size: 13px; color: #000;">
                  <img src="${logoURLCheckin}" alt="ACES Logo" style="width: 100px; margin-bottom: 10px;">
                  <p style="margin: 4px 0;">ACES Polytechnic College Inc.</p>
                  <p style="margin: 4px 0;">Panabo Circumferential Rd, San Francisco,</p>
                  <p style="margin: 4px 0;">Panabo City, Davao del Norte, Philippines</p>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <p style="margin: 4px 0;">Date and Time: 13/04/2025 06:55 PM</p>
                  <p style="margin: 4px 0;">Receipt no. <strong>00001</strong></p>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <table style="width: 100%; font-size: 12px; margin-bottom: 10px;">
                    <tr>
                      <th style="text-align: left;">Room Type</th>
                      <th>Qty</th>
                      <th style="text-align: right;">Price</th>
                    </tr>
                    <tr>
                      <td>Deluxe Room</td>
                      <td>x1</td>
                      <td style="text-align: right;">5500.00</td>
                    </tr>
                    <tr>
                      <td style="text-align: left;">No. of Days Stayed</td>
                      <td>x2</td>
                      <td style="text-align: right;">11000.00</td>
                    </tr>
                    <tr>
                      <td style="text-align: left;">Extra Pax</td>
                      <td></td>
                      <td style="text-align: right;">500</td>
                    </tr>
                    <tr>
                      <td style="text-align: left;"></td>
                      <td>x2</td>
                      <td style="text-align: right;">1000.00</td>
                    </tr>
                  </table>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <table style="width: 100%; font-size: 13px; font-weight: bold;">
                    <tr><td style="text-align: left;">Total</td><td></td><td style="text-align: right;">15000.00</td></tr>
                    <tr><td style="text-align: left;">Cash Tendered</td><td></td><td style="text-align: right;">15000.00</td></tr>
                    <tr><td style="text-align: left;">Change</td><td></td><td style="text-align: right;">0.00</td></tr>
                  </table>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <p style="margin-top: 10px;">Thank you!</p>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                </div>
              `,
              showConfirmButton: true,
              confirmButtonText: "Print Receipt",
              confirmButtonColor: "#1a2d1e",
              width: 360,
              padding: "1.5em",
              backdrop: false,
            });
          } else if (result.isDenied) {
            Swal.fire({
              title: "<strong>Finished activity on <br>time!</strong>",
              html: '<p style="color:#1a2d1e">Time Remaining: 1:12 Minutes<br>Time Consumed: 3:48 Minutes</p>',
              icon: "success",
              customClass: {
                confirmButton: "my-confirm-btn-checkin",
                title: "my-title-checkin",
              },
              confirmButtonText: "Close",
            });
          }
        });
      },
      error: function (error) {
        console.log("Check-in error:", error);
      },
    });
  });
});
