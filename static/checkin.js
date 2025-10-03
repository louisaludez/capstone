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
    opt.textContent = r.guest_name + " — Ref:" + r.ref + " — Room " + r.room + " — " + r.check_in_date + " → " + r.check_out_date;
    opt.setAttribute("data-id", r.id);
    if (r.guest_email) opt.setAttribute("data-email", r.guest_email);
    if (r.guest_address) opt.setAttribute("data-address", r.guest_address);
    opt.setAttribute("data-checkin", r.check_in_date);
    opt.setAttribute("data-checkout", r.check_out_date);
    opt.setAttribute("data-room", r.room);
    if (r.payment_method) opt.setAttribute("data-paymethod", r.payment_method);
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
  var cin = $opt.data("checkin") || "";
  var cout = $opt.data("checkout") || "";
  var room = ($opt.data("room") || "").toString().replace(/^R/, "");
  var payMethod = $opt.data("paymethod") || "";
  var billingAddr = $opt.data("billingaddr") || "";
  var balance = $opt.data("balance");
  if (email) $("#ci-guest-email").val(email);
  if (address) $("#ci-guest-address").val(address);
  if (cin) $("#ci-checkin-date").val(cin);
  if (cout) $("#ci-checkout-date").val(cout);
  if (room) $("#ci-room-type").val(room);
  if (payMethod) $("#ci-payment-method").val(payMethod).trigger("change");
  if (billingAddr) $("#ci-billing-address").val(billingAddr);
  if (typeof balance !== "undefined") $("#ci-current-balance").val(balance);
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
      // Safely clear this timer only
      if (checkInTimerInterval) {
        clearInterval(checkInTimerInterval);
        checkInTimerInterval = null;
      }
    }
  }, 1000);
}

function closeCheckinModal() {
  checkinOverlay.style.display = "none";
  if (checkInTimerInterval) {
    clearInterval(checkInTimerInterval);
    checkInTimerInterval = null;
  }
}

$(".ci-addons-decrease, .ci-addons-increase").on("click", function () {
  let count = parseInt($("#ci-addons-count").text());
  count += $(this).hasClass("ci-addons-increase") ? 1 : -1;
  if (count < 0) count = 0;
  $("#ci-addons-count").text(count);
});

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