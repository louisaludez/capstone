$(document).ready(function () {
  console.log("Document is ready");
  function updateCheckoutCardFields() {
    const paymentMethod = document.querySelector("#checkout #payment-method");
    const cardFields = document.querySelectorAll("#checkout .card-fields");
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

  const logoURLCheckout = document.getElementById("checkout").dataset.logoUrl;
  var checkoutModal = document.getElementById("checkout");
  var checkoutBtn = document.getElementById("check-out-modal-btn");
  var checkoutClose = document.getElementById("close-checkout-modal");
  let checkoutTimerInterval = null;

  checkoutBtn.onclick = function () {
    var fiveMinutes = 5 * 60,
      display = document.getElementById("checkout-timer");
    checkoutModal.style.display = "block";

    startCheckoutTimer(fiveMinutes, display);
    updateCheckoutCardFields();
  };

  checkoutClose.onclick = function () {
    checkoutModal.style.display = "none";
    clearInterval(checkoutTimerInterval);
    checkoutTimerInterval = null;
  };

  window.onclick = function (event) {
    if (event.target === checkoutModal) {
      checkoutModal.style.display = "none";
      clearInterval(checkoutTimerInterval);
      checkoutTimerInterval = null;
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    const paymentMethod = document.querySelector("#checkout #payment-method");
    updateCheckoutCardFields();
    paymentMethod.addEventListener("change", updateCheckoutCardFields);
  });

  function startCheckoutTimer(duration, display) {
    console.log("Starting checkout timer");
    var timer = duration,
      minutes,
      seconds;
    checkoutTimerInterval = setInterval(function () {
      minutes = parseInt(timer / 60, 10);
      seconds = parseInt(timer % 60, 10);
      minutes = minutes < 10 ? minutes : minutes;
      seconds = seconds < 10 ? "0" + seconds : seconds;

      display.textContent = minutes + ":" + seconds;
      console.log(display.textContent);
      if (--timer < 0) {
        timer = duration;
        clearInterval(checkoutTimerInterval);
        checkoutTimerInterval = null;
        checkoutModal.style.display = "none";
        Swal.fire({
          title: `<h1 style="color:red;">Activity Failed</h1>`,
          text: "Please complete the check-out process.",
          showCloseButton: true,
          confirmButtonText: `<i class="fa fa-thumbs-up"></i> Close`,
          html: "<p>Time Remaining : 0:00 Minutes<br>Time Consumed : 5:00 Minutes</p>",
          icon: "error",
          customClass: {
            confirmButton: "my-confirm-btn-checkout",
          },
        });
      }
    }, 1000);
  }

  document
    .getElementById("checkout-room")
    .addEventListener("click", function (event) {
      event.preventDefault();
      clearInterval(checkoutTimerInterval);
      checkoutTimerInterval = null;
      checkoutModal.style.display = "none";
      Swal.fire({
        title: "Room Successfully Checked Out!",
        text: "Your check-out has been completed.",
        html: '<p style="color:#1a2d1e">Guest: Juan Dela Cruz<br>Room no. 01<br>Reference no. 00001</p>',
        icon: "success",
        customClass: {
          confirmButton: "my-confirm-btn-checkout",
          denyButton: "my-deny-btn-checkout",
          title: "my-title-checkout",
          text: "my-text-checkout",
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
              <img src="${logoURLCheckout}" alt="ACES Logo" style="width: 100px; margin-bottom: 10px;">
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
              confirmButton: "my-confirm-btn-checkout",
              title: "my-title-checkout",
            },
            confirmButtonText: "Close",
          });
        }
      });
    });

  $(".guests-name-checkout").on("change", function () {
    console.log("changed");
    console.log("guest id:", $(this).val());
  });
});
