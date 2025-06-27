document
  .getElementById("view-reservations-btn")
  .addEventListener("click", function () {
    Swal.fire({
      title:
        '<strong style="font-size: 28px;">Reservations</strong><br><span style="font-size: 16px;">May 1, 2025</span>',
      html: `
    <div style="overflow-x:auto; font-family: sans-serif;">
      <table style="width:100%; border-collapse: collapse; text-align: left; font-size: 12px; color: #1a2d1e;">
        <thead>
          <tr style="background-color: #f0f0f0;">
            <th style="padding: 8px; text-align:center;">Reference No.</th>
            <th style="padding: 8px; text-align:center;">Guests Name</th>
            <th style="padding: 8px; text-align:center;">Service</th>
            <th style="padding: 8px; text-align:center;">Reservation Date</th>
            <th style="padding: 8px; text-align:center;">Check-in Date</th>
            <th style="padding: 8px; text-align:center;">Time-in</th>
            <th style="padding: 8px; text-align:center;">Status</th>
          </tr>
        </thead>
        <tbody>
          ${generateRow(
            "00001",
            "Juan Dela Cruz",
            "Reservation",
            "5/1/2025",
            "5/2/2025",
            "9:00AM",
            "Cancelled"
          )}
          ${generateRow(
            "00002",
            "Juan Dela Cruz",
            "Reservation",
            "5/1/2025",
            "5/2/2025",
            "9:00AM",
            "Checked-in"
          )}
          ${generateRow(
            "00003",
            "Juan Dela Cruz",
            "Reservation",
            "5/1/2025",
            "5/2/2025",
            "9:00AM",
            "Pending"
          )}
          ${generateRow(
            "00004",
            "Juan Dela Cruz",
            "Reservation",
            "5/1/2025",
            "5/2/2025",
            "9:00AM",
            "Checked-in"
          )}
          ${generateRow(
            "00005",
            "Juan Dela Cruz",
            "Reservation",
            "5/1/2025",
            "5/2/2025",
            "9:00AM",
            "Pending"
          )}
        </tbody>
      </table>
      <div style="margin-top: 10px; text-align: right; font-size: 12px;">
        <button style="margin: 2px;" class="btn btn-light">&lt;</button>
        <button style="margin: 2px; background: #ddd;" class="btn btn-light">1</button>
        <button style="margin: 2px;" class="btn btn-light">2</button>
        <button style="margin: 2px;" class="btn btn-light">3</button>
        <span style="margin: 2px;">...</span>
        <button style="margin: 2px;" class="btn btn-light">100</button>
        <button style="margin: 2px;" class="btn btn-light">&gt;</button>
      </div>
    </div>
  `,
      width: "60%",
      showCloseButton: true,
      showConfirmButton: false,
    });

    function generateRow(ref, name, service, rDate, cDate, time, status) {
      let color =
        {
          Cancelled: "background-color:#ad0908;color:#ffffff;",
          "Checked-in": "background-color:#7eb455; color:#ffffff;",
          Pending: "background-color:#d4c21a;color:#ffffff;",
        }[status] || "";
      return `
    <tr style="border-bottom: 1px solid #ddd;">
      <td style="padding: 8px; text-align:center;">${ref}</td>
      <td style="padding: 8px; text-align:center;">${name}</td>
      <td style="padding: 8px; text-align:center;">${service}</td>
      <td style="padding: 8px; text-align:center;">${rDate}</td>
      <td style="padding: 8px; text-align:center;">${cDate}</td>
      <td style="padding: 8px; text-align:center;">${time}</td>
      <td style="padding: 8px; text-align:center;">
        <span style="padding: 4px 8px; border-radius: 5px; font-weight: bold; ${color}">
          ${status}
        </span>
      </td>
    </tr>

  `;
    }
  });
