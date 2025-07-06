document
  .getElementById("checkin-rooms")
  .addEventListener("click", function (event) {
    clearInterval(checkinTimerInterval);
    checkinTimerInterval = null;
    checkinModal.style.display = "none";
    Swal.fire({
      title: "Room Successfully Checked In!",
      text: "Your check-in has been completed.",
      html: '<p style="color:#1a2d1e">Guest: Juan Dela Cruz<br>Room no. 01<br>Reference no. 00001</p>',
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
  });
