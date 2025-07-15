flatpickr("#ci-dob", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkout", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-guest-birth", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkin-date", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkout-date", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-exp-date", { dateFormat: "Y-m-d", allowInput: true });
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
const timerDisplayCheckIn = document.querySelector(".checkin-countdown-time");
let checkInTimerInterval = null;
document
  .getElementById("check-in-modal-btn")
  .addEventListener("click", function () {
    var minutes = 5 * 60;
    console.log("Check button clicked");
    checkinOverlay.style.display = "flex";
    timerDisplayCheckIn.textContent = "5:00";
    startCheckInTimer(minutes, timerDisplayCheckIn); // Start the timer when the modal opens
    
    
  });
checkinOverlay.addEventListener("click", function (e) {
  if (!checkinModal.contains(e.target)) {
    checkinOverlay.style.display = "none";
    
    closeCheckinModal();
    console.log(
      "modal closed clicked outside the modal the time should stop now!"
    ); // Reset the interval variable
  }
});

function startCheckInTimer(duration, display) {
  if (checkInTimerInterval) {
    clearInterval(checkInTimerInterval);
  }
  let timer = duration - 1,
    minutes,
    seconds;
  checkInTimerInterval = setInterval(function () {
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

function closeCheckinModal() {
  checkinOverlay.style.display = "none";
  clearInterval(InTimerInterval);
  checkInTimerInterval = null;
  }

$(".ci-addons-decrease, .ci-addons-increase").on("click", function () {
  let count = parseInt($("#ci-addons-count").text());
  count += $(this).hasClass("ci-addons-increase") ? 1 : -1;
  if (count < 0) count = 0;
  $("#ci-addons-count").text(count);
});

  $(".checkin-book-btn").on("click", function (event) {
    
    checkinModal.style.display = "none";
     const data = {
       guest_name: $("#ci-guest-name").val(),
       guest_address: $("#ci-guest-address").val(),
       guest_mobile: $("#ci-guest-mobile").val(),
       guest_birth: $("#ci-guest-birth").val(),
       guest_email: $("#ci-guest-email").val(),
       check_in: $("#ci-checkin-date").val(),
       check_out: $("#ci-checkout-date").val(),
       room: $("#ci-room-type").val(),
       total_guests: $("#ci-total-guests").val(),
       adults: $("#ci-no-of-adults").val(),
       children: $("#ci-no-of-children").val(),
       add_ons: $("#ci-addons-count").text(),
       children_7_years: $("#ci-children-below-7").val(),
       payment_method: $("#ci-payment-method").val(),
       card_number: $("#ci-card-number").val(),
       exp_date: $("#ci-exp-date").val(),
       cvv: $("#ci-cvc").val(),
       billing_address: $("#ci-billing-address").val(),
       current_balance: $("#ci-current-balance").val(),
       csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
     };

    $.ajax({
      type: "POST",
      url: "/staff/book-room/",
      data: data,

      success: function (response) {
        Swal.fire({
          title: "Room Successfully Checked In!",
          text: "Your check-in has been completed.",
          html: `<p style="color:#1a2d1e">Guest: ${data.guest_name}<br>Room no. ${data.room}<br>Reference no. 00001</p>`,
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