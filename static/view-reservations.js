// When "View Reservations" button is clicked
$("#view-reservations-btn").on("click", function () {
  loadReservations(1, true); // true = open modal
});

// Load reservation data with optional modal open
function loadReservations(page = 1, openModal = false) {
  $.ajax({
    url: "/ajax/get-reservations/",
    method: "GET",
    data: { page: page },
    dataType: "json",
    success: function (data) {
      const reservations = data.reservations;

      const rowsHtml =
        reservations.length > 0
          ? reservations
              .map((res) =>
                generateRow(
                  res.ref,
                  res.name,
                  res.service,
                  res.reservation_date,
                  res.checkin_date,
                  res.timein,
                  res.status
                )
              )
              .join("")
          : `
          <tr>
            <td colspan="7" style="text-align: center; padding: 20px; color: #777;">
              No reservations found on this page.
            </td>
          </tr>
        `;

      const pageInfoText = `
        <p style="text-align: right; margin: 10px 0; font-size: 12px; color: #444;">
          Page ${data.current_page} of ${data.num_pages}
          ${data.current_page == data.num_pages ? " — End of records" : ""}
        </p>
      `;

      const paginationHtml = generatePagination(
        data.current_page,
        data.num_pages,
        data.has_previous,
        data.has_next
      );

      const fullHtml = `
        <div style="overflow-x:auto; font-family: sans-serif; min-height: 300px; position: relative;">
          <style>
            tbody tr:hover {
              background-color: #f0f0f0;
              cursor: pointer;
              transition: background-color 0.2s ease;
            }
          </style>

          <table style="width:100%; border-collapse: collapse; text-align: left; font-size: 14px; color: #1a2d1e;">
            <thead>
              <tr style="background-color: #eaeaea;">
                <th style="padding: 12px; text-align:center;">Reference No.</th>
                <th style="padding: 12px; text-align:center;">Guests Name</th>
                <th style="padding: 12px; text-align:center;">Service</th>
                <th style="padding: 12px; text-align:center;">Reservation Date</th>
                <th style="padding: 12px; text-align:center;">Check-in Date</th>
                <th style="padding: 12px; text-align:center;">Time-in</th>
                <th style="padding: 12px; text-align:center;">Status</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
          ${pageInfoText}
          ${paginationHtml}
        </div>
      `;

      if (openModal) {
        Swal.fire({
          title:
            `<strong style="font-size: 28px;">Reservations</strong><br>` +
            `<span style="font-size: 16px;">${getToday()}</span>`,
          html: fullHtml,
          width: "70%",
          showCloseButton: false,
          showConfirmButton: false,
          didRender: () => {
            bindPaginationEvents();
            bindArrowCloseEvent();
          },
        });
      } else {
        Swal.update({
          title:
            `<strong style="font-size: 28px;">Reservations</strong><br>` +
            `<span style="font-size: 16px;">${getToday()}</span>`,
          html: fullHtml,
          didRender: () => {
            bindPaginationEvents();
            bindArrowCloseEvent();
          },
        });
      }
    },
    error: function () {
      Swal.fire("Error", "Failed to load reservations.", "error");
    },
  });
}

// Generate a row
function generateRow(ref, name, service, rDate, cDate, time, status) {
  let color =
    {
      Cancelled: "background-color:#ad0908;color:#ffffff;",
      "Checked-in": "background-color:#7eb455; color:#ffffff;",
      Pending: "background-color:#d4c21a;color:#ffffff;",
    }[status] || "";

  return `
    <tr style="border-bottom: 1px solid #ddd;">
      <td style="padding: 12px; text-align:center;">${ref}</td>
      <td style="padding: 12px; text-align:center;">${name}</td>
      <td style="padding: 12px; text-align:center;">${service}</td>
      <td style="padding: 12px; text-align:center;">${rDate}</td>
      <td style="padding: 12px; text-align:center;">${cDate}</td>
      <td style="padding: 12px; text-align:center;">${time}</td>
      <td style="padding: 12px; text-align:center;">
        <span style="padding: 4px 8px; border-radius: 5px; font-weight: bold; ${color}">
          ${status}
        </span>
      </td>
    </tr>
  `;
}

// Generate pagination
function generatePagination(current, total, hasPrev, hasNext) {
  let html = `<div style="margin-top: 10px; text-align: right; font-size: 12px;">`;

  if (hasPrev) {
    html += `<button class="btn btn-light pagination-btn" data-page="${
      current - 1
    }" style="margin: 2px;">&laquo;</button>`;
  }

  const range = 2;
  const start = Math.max(1, current - range);
  const end = Math.min(total, current + range);

  for (let i = start; i <= end; i++) {
    html += `<button class="btn btn-light pagination-btn" data-page="${i}" style="margin: 2px; ${
      i === current ? "background-color:#ccc;" : ""
    }">${i}</button>`;
  }

  if (hasNext) {
    html += `<button class="btn btn-light pagination-btn" data-page="${
      current + 1
    }" style="margin: 2px;">&raquo;</button>`;
  }

  html += `</div>`;
  return html;
}

// Handle pagination clicks
function bindPaginationEvents() {
  $(".pagination-btn").on("click", function () {
    const page = $(this).data("page");
    loadReservations(page, false); // don't reopen modal
  });
}

// Add arrow to top-right of modal and bind close
function bindArrowCloseEvent() {
  if ($("#close-arrow").length === 0) {
    const arrow = $(
      `<img id="close-arrow" src="${arrowIconUrl}" alt="Close" />`
    );
    arrow.css({
      position: "absolute",
      top: "15px",
      right: "20px",
      width: "24px",
      height: "24px",
      cursor: "pointer",
      zIndex: 9999,
    });
    $(".swal2-popup").append(arrow);

    arrow.on("click", function () {
      Swal.close();
    });
  }
}
function getToday() {
  const options = { year: "numeric", month: "long", day: "numeric" };
  return new Date().toLocaleDateString("en-US", options);
}
