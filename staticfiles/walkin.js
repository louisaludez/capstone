function updateCardFields() {
  const paymentMethod = document.getElementById("payment-method");
  const cardFields = document.querySelectorAll(".card-fields");
  if (paymentMethod.value === "credit-card") {
    cardFields.forEach((field) => {
      field.hidden = false; // Show the field
    });
  } else {
    cardFields.forEach((field) => {
      field.hidden = true; // Hide the field
    });
  }
}
const logoURL = document.getElementById("walkin").dataset.logoUrl;
var modal = document.getElementById("walkin");
var btn = document.getElementById("walkin-modal-btn");
var span = document.getElementById("close-walkin-modal");
let walkInTimerInterval = null;

btn.onclick = function () {
  var fivemunutes = 5 * 60,
    display = document.getElementById("walkin-timer"); // 5 minutes in seconds
  modal.style.display = "block";

  startWalkInTimer(fivemunutes, display); // Start the timer when the modal opens
  updateCardFields();
};
span.onclick = function () {
  modal.style.display = "none";
  clearInterval(walkInTimerInterval); // Clear the timer when modal is closed
  walkInTimerInterval = null; // Reset the interval variable
};
window.onclick = function (event) {
  if (event.target === modal) {
    modal.style.display = "none";
    clearInterval(walkInTimerInterval); // Clear the timer when modal is closed
    walkInTimerInterval = null; // Reset the interval variable
  }
};

document.addEventListener("DOMContentLoaded", function () {
  const paymentMethod = document.getElementById("payment-method");
  updateCardFields();
  paymentMethod.addEventListener("change", updateCardFields);
});

function startWalkInTimer(duration, display) {
  var timer = duration,
    minutes,
    seconds;
  walkInTimerInterval = setInterval(function () {
    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);
    minutes = minutes < 10 ? minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    display.textContent = minutes + ":" + seconds;
    console.log(display.textContent);
    if (--timer < 0) {
      timer = duration;
      clearInterval(walkInTimerInterval);
      walkInTimerInterval = null;
      modal.style.display = "none"; // Close the modal when time is up
      Swal.fire({
        title: `<h1 style="color:red;">Activity Failed</h1>`,
        text: "Please complete the walk-in process.",
        showCloseButton: true,
        confirmButtonText: `
                                                                                                                                                                                                                                              <i class="fa fa-thumbs-up"></i> Close
                                                                                                                                                                                                                                            `,
        html: "<p>Time Remaining : 0:00 Minutes<br>Time Consumed : 5:00 Minutes</p>",
        icon: "error",
        customClass: {
          confirmButton: "my-confirm-btn-walkin",
        },
      });
    }
  }, 1000);
}

document
  .getElementById("book-room")
  .addEventListener("click", function (event) {
    event.preventDefault(); // Prevent default form submission
    clearInterval(walkInTimerInterval);
    walkInTimerInterval = null;
    modal.style.display = "none";
    Swal.fire({
      title: "Room  Successfully Booked!",
      text: "Your room has been booked.",
      html: '<p style="color:#1a2d1e">Transaction recorded! <i>Guest Name: Juan Dela Cruz</i><br>Room no. 01<br>Reference no. 00001</p>',
      icon: "success",
      customClass: {
        confirmButton: "my-confirm-btn-booking",
        denyButton: "my-deny-btn-booking",
        title: "my-title-booking",
        text: "my-text-booking",
      },
      denyButtonColor: "green",
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
                                
                                <img src="${logoURL}" alt="ACES Logo" style="width: 100px; margin-bottom: 10px;">
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
                                      <td style="text-align: left;">No.of Days Stayed</td>
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
                                  </table>
                                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                                  <table style="width: 100%; font-size: 13px; font-weight: bold;">
                                    <tr><td style="text-align: left;">Total</td><td></td><td style="text-align: right;">15000.00</td></tr>
                                    <tr><td style="text-align: left;">Cash Tendered</td><td></td><td style="text-align: right;">15000.00</td></tr>
                                    <tr><td style="text-align: left;">Change</td><td></td><td style="text-align: right;">0.00</td></tr>
                                  </table>
                                  <hr style="border: 1px dashed rgb(0, 0, 0); margin: 10px 0;">
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
            confirmButton: "my-confirm-btn-booking",
            title: "my-title-booking",
          },
          confirmButtonText: "Close",
        });
      }
    });
  });
