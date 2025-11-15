flatpickr("#ci-dob", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkout", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-guest-birth", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkin-date", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-checkout-date", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#ci-exp-date", { dateFormat: "Y-m-d", allowInput: true });
const ciPaymentMethod = document.querySelector(".checkin-payment-method");
const ciCardFields = document.querySelector(".checkin-card-fields");
const ciNameInput = document.getElementById("ci-guest-name");
const ciBookingIdInput = document.getElementById("ci-booking-id");
let ciReservationsCache = [];

function populateCISelect(reservations) {
  if (!ciNameInput) return;
  ciNameInput.innerHTML = "";
  var placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select reserved customer";
  placeholder.disabled = true;
  placeholder.selected = true;
  ciNameInput.appendChild(placeholder);

  reservations.forEach(function (r) {
    var opt = document.createElement("option");
    opt.value = r.guest_name;
    opt.textContent = r.guest_name; // show only the guest name
    opt.setAttribute("data-id", r.id);
    // Optional details for auto-fill
    if (typeof r.guest_mobile !== "undefined" && r.guest_mobile !== null) opt.setAttribute("data-mobile", r.guest_mobile);
    else if (typeof r.mobile !== "undefined" && r.mobile !== null) opt.setAttribute("data-mobile", r.mobile);
    if (typeof r.total_guests !== "undefined") opt.setAttribute("data-totalguests", r.total_guests);
    else if (typeof r.total_of_guests !== "undefined") opt.setAttribute("data-totalguests", r.total_of_guests);
    if (typeof r.num_of_adults !== "undefined") opt.setAttribute("data-adults", r.num_of_adults);
    if (typeof r.num_of_children !== "undefined") opt.setAttribute("data-children", r.num_of_children);
    if (typeof r.children_below_7 !== "undefined") opt.setAttribute("data-children7", r.children_below_7);
    else if (typeof r.no_of_children_below_7 !== "undefined") opt.setAttribute("data-children7", r.no_of_children_below_7);
    if (r.guest_email) opt.setAttribute("data-email", r.guest_email);
    if (r.guest_address) opt.setAttribute("data-address", r.guest_address);
    opt.setAttribute("data-checkin", r.check_in_date);
    opt.setAttribute("data-checkout", r.check_out_date);
    opt.setAttribute("data-room", r.room);
    if (r.payment_method) opt.setAttribute("data-paymethod", r.payment_method);
    opt.setAttribute("data-cardnumber", r.card_number || "");
    opt.setAttribute("data-cardexp", r.card_exp || "");
    opt.setAttribute("data-cardcvc", r.card_cvc || "");
    if (r.billing_address) opt.setAttribute("data-billingaddr", r.billing_address);
    if (typeof r.total_balance !== "undefined") opt.setAttribute("data-balance", r.total_balance);
    ciNameInput.appendChild(opt);
  });
}

function loadPendingReservations(query) {
  return $.getJSON("/guestbooking/api/list-pending-reservations/", { q: query || "" })
    .done(function (resp) {
      ciReservationsCache = resp && resp.reservations ? resp.reservations : [];
      try { console.log("[checkin] guestbooking pending reservations:", ciReservationsCache); } catch (e) { }
      if (ciReservationsCache.length === 0) {
        // Fallback to staff reservations endpoint (filter Pending)
        return $.getJSON("/staff/ajax/get-reservations/")
          .done(function (staffResp) {
            var list = (staffResp && staffResp.reservations) ? staffResp.reservations : [];
            ciReservationsCache = list
              .filter(function (r) { return (r.status || "").toLowerCase() === "pending"; })
              .map(function (r) {
                // Map to expected shape; room not provided here
                var id = parseInt(r.ref, 10);
                return {
                  id: isNaN(id) ? null : id,
                  ref: r.ref,
                  guest_name: r.name,
                  guest_email: null,
                  guest_address: null,
                  check_in_date: (r.checkin_date || "").replace(/\//g, function (m) { return m; }),
                  check_out_date: "",
                  room: "",
                  status: r.status,
                  payment_method: null,
                  billing_address: null,
                  card_number: null,
                  card_exp: null,
                  card_cvc: null,
                  total_balance: null
                };
              });
            try { console.log("[checkin] staff fallback pending reservations:", ciReservationsCache); } catch (e) { }
            populateCISelect(ciReservationsCache);
          })
          .fail(function () {
            try { console.error("[checkin] staff fallback failed"); } catch (e) { }
            populateCISelect([]);
          });
      }
      populateCISelect(ciReservationsCache);
    })
    .fail(function () {
      // Fallback if guestbooking API fails
      $.getJSON("/staff/ajax/get-reservations/")
        .done(function (staffResp) {
          var list = (staffResp && staffResp.reservations) ? staffResp.reservations : [];
          ciReservationsCache = list
            .filter(function (r) { return (r.status || "").toLowerCase() === "pending"; })
            .map(function (r) {
              var id = parseInt(r.ref, 10);
              return {
                id: isNaN(id) ? null : id,
                ref: r.ref,
                guest_name: r.name,
                guest_email: null,
                guest_address: null,
                check_in_date: (r.checkin_date || "").replace(/\//g, function (m) { return m; }),
                check_out_date: "",
                room: "",
                  status: r.status,
                  payment_method: null,
                  billing_address: null,
                  card_number: null,
                  card_exp: null,
                  card_cvc: null,
                  total_balance: null
              };
            });
          try { console.log("[checkin] staff fallback (api fail) pending reservations:", ciReservationsCache); } catch (e) { }
          populateCISelect(ciReservationsCache);
        })
        .fail(function () {
          ciReservationsCache = [];
          try { console.error("[checkin] both APIs failed; no reservations loaded"); } catch (e) { }
          populateCISelect([]);
        });
    });
}

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

document
  .getElementById("check-in-modal-btn")
  .addEventListener("click", function () {
    console.log("Check button clicked");
    checkinOverlay.style.display = "flex";
    // Load latest pending reservations for selection
    loadPendingReservations("");

    // Ensure addons popup is hidden initially
    try { $("#checkin-addons-popup").hide(); } catch (e) { }


  });
// When a name is chosen, map it to the reservation and prefill details
$(document).on("change", "#ci-guest-name", function () {
  var $opt = $("#ci-guest-name option:selected");
  if (!$opt.length || $opt.val() === "") {
    $("#ci-booking-id").val("");
    return;
  }
  var id = $opt.data("id");
  $("#ci-booking-id").val(id || "");
  // Prefill optional fields
  var email = $opt.data("email") || "";
  var address = $opt.data("address") || "";
  var mobile = $opt.data("mobile") || "";
  var cin = $opt.data("checkin") || "";
  var cout = $opt.data("checkout") || "";
  var room = ($opt.data("room") || "").toString().replace(/^R/, "");
  var payMethod = $opt.data("paymethod") || "";
  var billingAddr = $opt.data("billingaddr") || "";
  var balance = $opt.data("balance");
  var cardNumber = $opt.data("cardnumber") || "";
  var cardExp = $opt.data("cardexp") || "";
  var cardCvc = $opt.data("cardcvc") || "";
  var totalGuests = $opt.data("totalguests");
  var adults = $opt.data("adults");
  var children = $opt.data("children");
  var children7 = $opt.data("children7");
  if (email) $("#ci-guest-email").val(email);
  if (address) $("#ci-guest-address").val(address);
  if (mobile) $("#ci-guest-mobile").val(mobile);
  if (typeof totalGuests !== "undefined") $("#ci-total-guests").val(totalGuests);
  if (typeof adults !== "undefined") $("#ci-no-of-adults").val(adults);
  if (typeof children !== "undefined") $("#ci-no-of-children").val(children);
  if (typeof children7 !== "undefined") $("#ci-children-below-7").val(children7);
  if (cin) $("#ci-checkin-date").val(cin);
  if (cout) $("#ci-checkout-date").val(cout);
  if (room) $("#ci-room-type").val(room);
  if (payMethod) $("#ci-payment-method").val(payMethod).trigger("change");
  if (billingAddr) $("#ci-billing-address").val(billingAddr);
  if (typeof balance !== "undefined") $("#ci-current-balance").val(balance);
  if ((payMethod || "").toLowerCase() === "card") {
    $("#ci-card-number").val(cardNumber || "");
    $("#ci-exp-date").val(cardExp || "");
    $("#ci-cvc").val(cardCvc || "");
  } else {
    $("#ci-card-number").val("");
    $("#ci-exp-date").val("");
    $("#ci-cvc").val("");
  }
  // Debug print of all gathered details for the selected guest/reservation
  try {
    const selectedName = $("#ci-guest-name").val();
    const debugDetails = {
      id: id || null,
      name: selectedName || "",
      email: email || "",
      address: address || "",
      mobile: mobile || "",
      check_in_date: cin || "",
      check_out_date: cout || "",
      room: room || "",
      totalGuests: typeof totalGuests !== "undefined" ? totalGuests : "",
      adults: typeof adults !== "undefined" ? adults : "",
      children: typeof children !== "undefined" ? children : "",
      childrenBelow7: typeof children7 !== "undefined" ? children7 : "",
      payMethod: payMethod || "",
      billingAddress: billingAddr || "",
      balance: typeof balance !== "undefined" ? balance : ""
    };
    console.log("[checkin] Selected guest details:", debugDetails);
    if (console.table) console.table(debugDetails);
    console.log("[checkin] Raw data-* attributes:", $opt.data());
  } catch (e) {
    try { console.warn("[checkin] debug print failed", e); } catch (_) { }
  }
});
checkinOverlay.addEventListener("click", function (e) {
  if (!checkinModal.contains(e.target)) {
    checkinOverlay.style.display = "none";
    closeCheckinModal();
  }
});

function closeCheckinModal() {
  checkinOverlay.style.display = "none";

}

$(".ci-addons-decrease, .ci-addons-increase").on("click", function () {
  let count = parseInt($("#ci-addons-count").text());
  count += $(this).hasClass("ci-addons-increase") ? 1 : -1;
  if (count < 0) count = 0;
  $("#ci-addons-count").text(count);
});

// Print check-in receipt function
function printCheckinReceipt(data, receiptNumber) {
  // Calculate date and time
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  
  // Calculate days stayed
  const checkIn = new Date(data.check_in);
  const checkOut = new Date(data.check_out);
  const daysStayed = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
  
  // Room type to price mapping
  const roomPrices = {
    'Standard': 1500,
    'Family': 2500,
    'Deluxe': 4500
  };
  
  // Extract room type from room selection
  const roomSelect = document.getElementById('ci-room-type');
  let roomType = 'Deluxe';
  let roomPrice = 4500;
  
  if (roomSelect && roomSelect.options[roomSelect.selectedIndex]) {
    const roomText = roomSelect.options[roomSelect.selectedIndex].text;
    if (roomText.includes('Standard')) {
      roomType = 'Standard';
      roomPrice = roomPrices.Standard;
    } else if (roomText.includes('Family')) {
      roomType = 'Family';
      roomPrice = roomPrices.Family;
    } else if (roomText.includes('Deluxe')) {
      roomType = 'Deluxe';
      roomPrice = roomPrices.Deluxe;
    }
  }
  
  // Calculate add-on totals (ensure values are parsed as numbers)
  const addonsData = window.checkinAddonsData || { bed: 0, pillow: 0, towel: 0 };
  const bedCount = parseInt(addonsData.bed || 0, 10);
  const pillowCount = parseInt(addonsData.pillow || 0, 10);
  const towelCount = parseInt(addonsData.towel || 0, 10);
  const bedTotal = bedCount * 200;
  const pillowTotal = pillowCount * 50;
  const towelTotal = towelCount * 30;
  const addonTotal = bedTotal + pillowTotal + towelTotal;
  
  // Use the actual balance from the form
  const total = parseFloat(data.current_balance) || 0;
  
  // Calculate room total for display
  const roomTotal = roomPrice * daysStayed;
  
  // Get logo URL (fallback if not defined)
  const logoURL = typeof logoURLCheckin !== 'undefined' ? logoURLCheckin : '';
  
  // Create receipt HTML
  const receiptHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Receipt - ${receiptNumber}</title>
      <style>
        @media print {
          @page {
            size: A4;
            margin: 20mm;
          }
          body {
            margin: 0;
            padding: 20px;
          }
        }
        body {
          font-family: Arial, sans-serif;
          text-align: center;
          font-size: 18px;
          color: #000;
          padding: 20px;
          margin: 0;
          max-width: 800px;
          margin: 0 auto;
        }
        img {
          width: 150px;
          margin-bottom: 15px;
        }
        hr {
          border: 2px dashed #333;
          margin: 15px 0;
        }
        p {
          font-size: 18px;
          margin: 8px 0;
        }
        table {
          width: 100%;
          font-size: 16px;
          margin-bottom: 15px;
          border-collapse: collapse;
        }
        th {
          text-align: left;
          font-weight: bold;
          font-size: 18px;
          padding: 8px 0;
        }
        td {
          padding: 6px 0;
          font-size: 16px;
        }
        .total-table {
          font-size: 18px;
          font-weight: bold;
        }
        .total-table td {
          font-size: 18px;
          padding: 8px 0;
        }
        .text-left {
          text-align: left;
        }
        .text-right {
          text-align: right;
        }
        .text-center {
          text-align: center;
        }
        strong {
          font-size: 20px;
        }
      </style>
    </head>
    <body>
      ${logoURL ? `<img src="${logoURL}" alt="ACES Logo">` : ''}
      <p style="margin: 8px 0; font-size: 18px;">ACES Polytechnic College Inc.</p>
      <p style="margin: 8px 0; font-size: 18px;">Panabo Circumferential Rd, San Francisco,</p>
      <p style="margin: 8px 0; font-size: 18px;">Panabo City, Davao del Norte, Philippines</p>
      <hr>
      <p style="margin: 8px 0; font-size: 18px;">Date and Time: ${dateStr} ${timeStr}</p>
      <p style="margin: 8px 0; font-size: 18px;">Receipt no. <strong>${receiptNumber}</strong></p>
      <p style="margin: 8px 0; font-size: 18px;">Guest: <strong>${data.guest_name || 'N/A'}</strong></p>
      <p style="margin: 8px 0; font-size: 18px;">Room No. <strong>${data.room || 'N/A'}</strong></p>
      <hr>
      <table>
        <tr>
          <th class="text-left">Room Type</th>
          <th class="text-center">Qty</th>
          <th class="text-right">Price</th>
        </tr>
        <tr>
          <td class="text-left">${roomType} Room</td>
          <td class="text-center">x1</td>
          <td class="text-right">${roomPrice.toFixed(2)}</td>
        </tr>
        <tr>
          <td class="text-left">No. of Days Stayed</td>
          <td class="text-center">x${daysStayed}</td>
          <td class="text-right">${roomTotal.toFixed(2)}</td>
        </tr>
        ${bedCount > 0 ? `
        <tr>
          <td class="text-left">Extra Bed</td>
          <td class="text-center">x${bedCount}</td>
          <td class="text-right">${bedTotal.toFixed(2)}</td>
        </tr>
        ` : ''}
        ${pillowCount > 0 ? `
        <tr>
          <td class="text-left">Extra Pillow</td>
          <td class="text-center">x${pillowCount}</td>
          <td class="text-right">${pillowTotal.toFixed(2)}</td>
        </tr>
        ` : ''}
        ${towelCount > 0 ? `
        <tr>
          <td class="text-left">Extra Towel</td>
          <td class="text-center">x${towelCount}</td>
          <td class="text-right">${towelTotal.toFixed(2)}</td>
        </tr>
        ` : ''}
      </table>
      <hr>
      <table class="total-table">
        <tr>
          <td class="text-left">Total</td>
          <td></td>
          <td class="text-right">${total.toFixed(2)}</td>
        </tr>
        <tr>
          <td class="text-left">Payment Method</td>
          <td></td>
          <td class="text-right">${(data.payment_method || 'cash').charAt(0).toUpperCase() + (data.payment_method || 'cash').slice(1)}</td>
        </tr>
      </table>
      <hr>
      <p style="margin-top: 15px; font-size: 18px;">Thank you!</p>
      <hr>
    </body>
    </html>
  `;
  
  // Open print window
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to print the receipt.');
    return;
  }
  
  printWindow.document.write(receiptHTML);
  printWindow.document.close();
  
  // Function to handle printing and return focus to main window
  const triggerPrint = function() {
    try {
      printWindow.print();
      // Return focus to main window after a short delay
      setTimeout(function() {
        window.focus();
      }, 100);
    } catch (e) {
      console.error('Print error:', e);
      window.focus();
    }
  };

  // Wait for content to load, then print
  // Use both onload and a timeout as fallback
  printWindow.onload = function() {
    setTimeout(triggerPrint, 250);
  };
  
  // Fallback: if onload doesn't fire, try printing after a delay
  setTimeout(function() {
    if (printWindow.document.readyState === 'complete' || printWindow.document.readyState === 'interactive') {
      if (!printWindow.document.body || printWindow.document.body.innerHTML === '') {
        return; // Content not ready yet
      }
      triggerPrint();
    }
  }, 500);
  
  // Ensure main window regains focus even if print dialog is cancelled
  // Listen for when print window closes or loses focus
  const checkPrintWindow = setInterval(function() {
    if (printWindow.closed) {
      clearInterval(checkPrintWindow);
      window.focus();
    }
  }, 500);
  
  // Clean up interval after 10 seconds
  setTimeout(function() {
    clearInterval(checkPrintWindow);
    window.focus();
  }, 10000);
}

$(".checkin-book-btn").on("click", function (event) {

  var bookingId = $("#ci-booking-id").val();
  if (!bookingId) {
    Swal.fire({
      icon: "error",
      title: "Reservation required",
      text: "Select an existing reservation to proceed with check-in.",
      confirmButtonColor: "#1a2d1e",
    });
    return;
  }

  checkinModal.style.display = "none";
  const data = {
    booking_id: bookingId,
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
    // Send detailed add-ons
    'add_ons[bed]': checkinAddonsData && typeof checkinAddonsData.bed !== 'undefined' ? checkinAddonsData.bed : 0,
    'add_ons[pillow]': checkinAddonsData && typeof checkinAddonsData.pillow !== 'undefined' ? checkinAddonsData.pillow : 0,
    'add_ons[towel]': checkinAddonsData && typeof checkinAddonsData.towel !== 'undefined' ? checkinAddonsData.towel : 0,
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
    url: "/guestbooking/api/checkin-reservation/",
    data: data,

    success: function (response) {
      Swal.fire({
        title: "Room Successfully Checked In!",
        text: "Your check-in has been completed.",
        html: `<p style="color:#1a2d1e">Guest: ${data.guest_name}<br>Room no. ${data.room}<br>Reference no. 00001</p>`,
        icon: "success",
        customClass: {
          confirmButton: "my-confirm-btn-checkin",
          title: "my-title-checkin",
          text: "my-text-checkin",
        },
        confirmButtonText: "View Receipt",
      }).then((result) => {
        if (result.isConfirmed) {
          // Calculate dynamic values for receipt
          const now = new Date();
          const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
          const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
          const receiptNumber = response.receipt_number || response.reference_number || "00001";
          
          // Calculate days stayed
          const checkIn = new Date(data.check_in);
          const checkOut = new Date(data.check_out);
          const daysStayed = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
          
          // Room type to price mapping
          const roomPrices = {
            'Standard': 1500,
            'Family': 2500,
            'Deluxe': 4500
          };
          
          // Extract room type from room selection
          const roomSelect = document.getElementById('ci-room-type');
          let roomType = 'Deluxe';
          let roomPrice = 4500;
          
          if (roomSelect && roomSelect.options[roomSelect.selectedIndex]) {
            const roomText = roomSelect.options[roomSelect.selectedIndex].text;
            if (roomText.includes('Standard')) {
              roomType = 'Standard';
              roomPrice = roomPrices.Standard;
            } else if (roomText.includes('Family')) {
              roomType = 'Family';
              roomPrice = roomPrices.Family;
            } else if (roomText.includes('Deluxe')) {
              roomType = 'Deluxe';
              roomPrice = roomPrices.Deluxe;
            }
          }
          
          // Calculate totals (ensure add-ons are parsed as numbers)
          const roomTotal = roomPrice * daysStayed;
          const addonsData = window.checkinAddonsData || { bed: 0, pillow: 0, towel: 0 };
          const bedCountPreview = parseInt(addonsData.bed || 0, 10);
          const pillowCountPreview = parseInt(addonsData.pillow || 0, 10);
          const towelCountPreview = parseInt(addonsData.towel || 0, 10);
          const bedTotal = bedCountPreview * 200;
          const pillowTotal = pillowCountPreview * 50;
          const towelTotal = towelCountPreview * 30;
          const total = parseFloat(data.current_balance) || (roomTotal + bedTotal + pillowTotal + towelTotal);
          
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
                  <p style="margin: 4px 0;">Date and Time: ${dateStr} ${timeStr}</p>
                  <p style="margin: 4px 0;">Receipt no. <strong>${receiptNumber}</strong></p>
                  <p style="margin: 4px 0;">Guest: <strong>${data.guest_name || 'N/A'}</strong></p>
                  <p style="margin: 4px 0;">Room No. <strong>${data.room || 'N/A'}</strong></p>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <table style="width: 100%; font-size: 12px; margin-bottom: 10px;">
                    <tr>
                      <th style="text-align: left;">Room Type</th>
                      <th>Qty</th>
                      <th style="text-align: right;">Price</th>
                    </tr>
                    <tr>
                      <td>${roomType} Room</td>
                      <td>x1</td>
                      <td style="text-align: right;">${roomPrice.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td style="text-align: left;">No. of Days Stayed</td>
                      <td>x${daysStayed}</td>
                      <td style="text-align: right;">${roomTotal.toFixed(2)}</td>
                    </tr>
                    ${bedCountPreview > 0 ? `
                    <tr>
                      <td style="text-align: left;">Extra Bed</td>
                      <td>x${bedCountPreview}</td>
                      <td style="text-align: right;">${bedTotal.toFixed(2)}</td>
                    </tr>
                    ` : ''}
                    ${pillowCountPreview > 0 ? `
                    <tr>
                      <td style="text-align: left;">Extra Pillow</td>
                      <td>x${pillowCountPreview}</td>
                      <td style="text-align: right;">${pillowTotal.toFixed(2)}</td>
                    </tr>
                    ` : ''}
                    ${towelCountPreview > 0 ? `
                    <tr>
                      <td style="text-align: left;">Extra Towel</td>
                      <td>x${towelCountPreview}</td>
                      <td style="text-align: right;">${towelTotal.toFixed(2)}</td>
                    </tr>
                    ` : ''}
                  </table>
                  <hr style="border: 1px dashed #333; margin: 10px 0;">
                  <table style="width: 100%; font-size: 13px; font-weight: bold;">
                    <tr><td style="text-align: left;">Total</td><td></td><td style="text-align: right;">${total.toFixed(2)}</td></tr>
                    <tr><td style="text-align: left;">Payment Method</td><td></td><td style="text-align: right;">${(data.payment_method || 'cash').charAt(0).toUpperCase() + (data.payment_method || 'cash').slice(1)}</td></tr>
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
          }).then((printResult) => {
            if (printResult.isConfirmed) {
              // Close SweetAlert first to prevent blocking
              Swal.close();
              // Small delay to ensure SweetAlert is fully closed before printing
              setTimeout(function() {
                // Get receipt number from response or use default
                const receiptNumber = response.receipt_number || response.reference_number || "00001";
                printCheckinReceipt(data, receiptNumber);
              }, 100);
            }
          });
        }
      });
    },
    error: function (error) {
      console.log("Check-in error:", error);
    },
  });
});

// === Check-in Add-ons dropdown behavior ===
// Toggle dropdown
$(document).on('click', '.checkin-addons-dropdown', function (e) {
  e.preventDefault();
  e.stopPropagation();
  const $popup = $('#checkin-addons-popup');
  const willOpen = !$popup.hasClass('show');
  console.log('[checkin] addons dropdown clicked — toggling popup (class-based)', { willOpen });
  $popup.toggleClass('show', willOpen);
});

// Close when clicking outside
$(document).on('click', function (e) {
  if (!$(e.target).closest('.checkin-addons-dropdown').length) {
    if ($('#checkin-addons-popup').hasClass('show')) {
      console.log('[checkin] click outside — closing addons popup');
    }
    $('#checkin-addons-popup').removeClass('show');
  }
});

// Plus/minus buttons inside popup
$(document).on('click', '#checkin-bed-minus, #checkin-bed-plus, #checkin-pillow-minus, #checkin-pillow-plus, #checkin-towel-minus, #checkin-towel-plus', function (e) {
  e.preventDefault();
  e.stopPropagation();
  const isPlus = this.id.includes('plus');
  const type = this.id.replace('checkin-', '').replace('-plus', '').replace('-minus', '');
  const delta = isPlus ? 1 : -1;
  console.log('[checkin] addons adjust', { type, delta });
  if (typeof changeCheckinAddon === 'function') {
    changeCheckinAddon(type, delta);
  }
});