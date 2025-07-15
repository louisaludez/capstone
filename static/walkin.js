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
  let  timer = duration - 1,
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
$(".wi-addons-decrease, .wi-addons-increase").on("click", function () {
  let count = parseInt($("#wi-addons-count").text());
  count += $(this).hasClass("wi-addons-increase") ? 1 : -1;
  if (count < 0) count = 0;
  $("#wi-addons-count").text(count);
});

 $(".walkin-book-btn").on("click", function (event) {
   walkinOverlay.style.display = "none";
   const data = {
     guest_name: document.querySelector(".walkin-name").value,
     guest_address: document.querySelector(".walkin-address").value,
     guest_mobile: document.querySelector(".walkin-mobile").value,
     guest_birth: document.querySelector(".walkin-birth").value,
     guest_email: document.querySelector(".walkin-email").value,
     check_in: document.querySelector(".walkin-check-in").value,
     check_out: document.querySelector(".walkin-check-out").value,
     room: document.querySelector(".walkin-room").value,
     total_guests: document.querySelector(".walkin-total-guest").value,
     adults: document.querySelector(".walkin-no-of-adults").value,
     children: document.querySelector(".walkin-no-of-children").value,
     add_ons: document.querySelector("#wi-addons-count").textContent,
     children_7_years: document.querySelector(".walkin-below-seven").value,
     payment_method: document.querySelector(".walkin-payment-method").value,
     card_number: document.querySelector(".walkin-card-number").value,
     exp_date: document.querySelector(".walkin-card-exp-date").value,
     cvc: document.querySelector(".walkin-card-cvc").value,
     billing_address: document.querySelector(".walkin-billing-address").value,
     current_balance: document.querySelector(".walkin-balance").value,
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