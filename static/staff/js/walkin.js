flatpickr("#dob", { dateFormat: "Y-m-d", allowInput: true });
var wiCheckinPicker = flatpickr("#checkin", { dateFormat: "Y-m-d", allowInput: true, minDate: "today" });
var wiCheckoutPicker = flatpickr("#checkout", { dateFormat: "Y-m-d", allowInput: true, minDate: "today" });

// Make flatpickr instances globally accessible
window.wiCheckinPicker = wiCheckinPicker;
window.wiCheckoutPicker = wiCheckoutPicker;

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

document
  .getElementById("walk-in-modal-btn")
  .addEventListener("click", function () {

    console.log("Walk-in button clicked");
    walkinOverlay.style.display = "flex";

    // Update room dropdown to disable rooms under maintenance or in housekeeping
    updateWalkinRoomDropdownAvailability();

    // Ensure flatpickr instances are working on date fields
    setTimeout(function () {
      const checkinInput = document.getElementById("checkin");
      const checkoutInput = document.getElementById("checkout");

      if (checkinInput && !checkinInput.disabled) {
        // Reinitialize if needed
        if (!window.wiCheckinPicker || !checkinInput._flatpickr) {
          try {
            if (window.wiCheckinPicker) window.wiCheckinPicker.destroy();
          } catch (e) { }
          window.wiCheckinPicker = flatpickr("#checkin", { dateFormat: "Y-m-d", allowInput: true, minDate: "today" });
        }
      }

      if (checkoutInput && !checkoutInput.disabled) {
        // Reinitialize if needed
        if (!window.wiCheckoutPicker || !checkoutInput._flatpickr) {
          try {
            if (window.wiCheckoutPicker) window.wiCheckoutPicker.destroy();
          } catch (e) { }
          window.wiCheckoutPicker = flatpickr("#checkout", { dateFormat: "Y-m-d", allowInput: true, minDate: "today" });
        }
      }

      // Update book button state when modal opens
      if (window.updateWalkinBookButtonState) {
        window.updateWalkinBookButtonState();
      }
    }, 100);

  });

// Function to update walk-in room dropdown based on current room statuses
function updateWalkinRoomDropdownAvailability() {
  const roomSelect = document.querySelector('.walkin-room');
  if (!roomSelect) return;

  console.log('[walkin] Updating room dropdown availability');

  // Get current date for room status check
  const today = new Date().toISOString().slice(0, 10);

  // Fetch current room statuses
  $.getJSON('/staff/api/room-status/', { date: today })
    .done(function (data) {
      console.log('[walkin] Room status data received:', data);

      // Disable rooms that are under maintenance or in housekeeping
      Array.from(roomSelect.options).forEach(function (option) {
        if (option.value === '' || option.value === null) return; // Skip placeholder

        const roomCode = option.value;
        const hkStatus = data.housekeeping_status && data.housekeeping_status[roomCode];

        if (hkStatus === 'under_maintenance' || hkStatus === 'in_progress') {
          option.disabled = true;
          option.style.color = '#999';
          option.style.backgroundColor = '#f0f0f0';
          // Add indicator to option text
          if (hkStatus === 'under_maintenance') {
            option.textContent = option.textContent.replace(/\s*\(.*\)$/, '') + ' (Under Maintenance)';
          } else if (hkStatus === 'in_progress') {
            option.textContent = option.textContent.replace(/\s*\(.*\)$/, '') + ' (In Housekeeping)';
          }
          console.log(`[walkin] Disabled room ${roomCode}: ${hkStatus}`);
        } else {
          option.disabled = false;
          option.style.color = '';
          option.style.backgroundColor = '';
          // Remove any status indicators
          option.textContent = option.textContent.replace(/\s*\(Under Maintenance\)$/, '')
            .replace(/\s*\(In Housekeeping\)$/, '');
        }
      });
    })
    .fail(function (error) {
      console.error('[walkin] Failed to fetch room status:', error);
    });
}
// Load availability when room changes
$(document).on("change", ".walkin-room", function () {
  var room = $(this).val();
  if (!room) return;
  try { console.log('[walkin] room changed ->', room); } catch (e) { }
  $.getJSON("/staff/api/room-availability/", { room: room })
    .done(function (resp) {
      try { console.log("[walkin] availability for room", room, resp); } catch (e) { }
      var blockedDatesSet = new Set();
      (resp.blocked || []).forEach(function (range) {
        (range.dates || []).forEach(function (d) { blockedDatesSet.add(d); });
      });
      try { console.log('[walkin] blockedDatesSet size =', blockedDatesSet.size, 'sample:', Array.from(blockedDatesSet).slice(0, 10)); } catch (e) { }

      // Recreate flatpickr with explicit disabled date strings so UI updates reliably
      var blockedDates = Array.from(blockedDatesSet);
      try { console.log('[walkin] blockedDates array ->', blockedDates); } catch (e) { }
      try { if (wiCheckinPicker) wiCheckinPicker.destroy(); } catch (e) { }
      try { if (wiCheckoutPicker) wiCheckoutPicker.destroy(); } catch (e) { }

      wiCheckinPicker = flatpickr("#checkin", {
        dateFormat: "Y-m-d",
        allowInput: true,
        minDate: "today",
        disable: blockedDates,
        onDayCreate: function (dObj, dStr, fp, dayElem) {
          if (!dayElem.dateObj) return;
          var y = dayElem.dateObj.getFullYear();
          var m = (dayElem.dateObj.getMonth() + 1).toString().padStart(2, '0');
          var dd = dayElem.dateObj.getDate().toString().padStart(2, '0');
          var key = y + '-' + m + '-' + dd;
          if (blockedDatesSet.has(key)) {
            dayElem.style.backgroundColor = '#ad0908';
            dayElem.style.color = '#ffffff';
            try { console.log('[walkin] marking blocked check-in day:', key); } catch (e) { }
          }
        },
        onChange: function (selectedDates, dateStr, fp) {
          var isBlocked = blockedDatesSet.has(dateStr);
          try { console.log('[walkin] check-in selected =', dateStr, 'isBlocked?', isBlocked); } catch (e) { }
          // Trigger balance calculation when check-in date changes
          if (typeof window.calculateBalance === 'function') {
            setTimeout(function () { window.calculateBalance(); }, 100);
          }
        }
      });

      wiCheckoutPicker = flatpickr("#checkout", {
        dateFormat: "Y-m-d",
        allowInput: true,
        minDate: "today",
        disable: blockedDates,
        onDayCreate: function (dObj, dStr, fp, dayElem) {
          if (!dayElem.dateObj) return;
          var y = dayElem.dateObj.getFullYear();
          var m = (dayElem.dateObj.getMonth() + 1).toString().padStart(2, '0');
          var dd = dayElem.dateObj.getDate().toString().padStart(2, '0');
          var key = y + '-' + m + '-' + dd;
          if (blockedDatesSet.has(key)) {
            dayElem.style.backgroundColor = '#ad0908';
            dayElem.style.color = '#ffffff';
            try { console.log('[walkin] marking blocked check-out day:', key); } catch (e) { }
          }
        },
        onChange: function (selectedDates, dateStr, fp) {
          var isBlocked = blockedDatesSet.has(dateStr);
          try { console.log('[walkin] check-out selected =', dateStr, 'isBlocked?', isBlocked); } catch (e) { }
          // Trigger balance calculation when check-out date changes
          if (typeof window.calculateBalance === 'function') {
            setTimeout(function () { window.calculateBalance(); }, 100);
          }
        }
      });

      // Clear previously selected dates when room changes
      try { console.log('[walkin] clearing previous dates for new room'); } catch (e) { }
      wiCheckinPicker.clear();
      wiCheckoutPicker.clear();
    })
    .fail(function (xhr) {
      try { console.error('[walkin] availability error', xhr.responseText); } catch (e) { }
    });
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

// function startWalkInTimer(duration, display) {
//   if (walkInTimerInterval) {
//     clearInterval(walkInTimerInterval);
//   }
//   let timer = duration - 1,
//     minutes,
//     seconds;
//   walkInTimerInterval = setInterval(function () {
//     minutes = parseInt(timer / 60, 10);
//     seconds = parseInt(timer % 60, 10);
//     minutes = minutes < 1 ? "" + minutes : minutes;
//     seconds = seconds < 10 ? "0" + seconds : seconds;


//     console.log(`Timer: ${minutes}:${seconds}`);
//     if (--timer < 0) {
//       timer = duration;
//       clearInterval(walkInTimerInterval);

//       // Hide the modal when the timer ends
//     }
//   }, 1000);
// // }

function closeWalkinModal() {
  walkinOverlay.style.display = "none";

}
// Add-ons dropdown functionality
window.addonsData = window.addonsData || {
  bed: 0,
  pillow: 0,
  towel: 0
};

// Initialize add-ons functionality when DOM is ready
$(document).ready(function () {
  // Toggle add-ons popup
  $(document).on("click", ".walkin-addons-dropdown", function (e) {
    e.preventDefault();
    e.stopPropagation();
    console.log("Add-ons dropdown clicked");
    $("#addons-popup").toggleClass('show');
  });

  // Add-ons counter functionality
  $(document).on("click", "#bed-minus, #bed-plus, #pillow-minus, #pillow-plus, #towel-minus, #towel-plus", function (e) {
    e.preventDefault();
    e.stopPropagation();
    console.log("Add-ons button clicked:", this.id);

    const isPlus = this.id.includes('plus');
    const type = this.id.replace('-plus', '').replace('-minus', '');

    let count = addonsData[type];
    count += isPlus ? 1 : -1;
    if (count < 0) count = 0;
    if (count > 10) count = 10;

    addonsData[type] = count;
    $(`#${type}-count`).text(count);

    // Update button states
    $(`#${type}-minus`).prop('disabled', count <= 0);
    $(`#${type}-plus`).prop('disabled', count >= 10);

    // Update summary
    updateAddonsSummary();

    // Trigger balance recalculation if calculateBalance function exists
    if (typeof calculateBalance === 'function') {
      calculateBalance();
    } else if (typeof window.calculateBalance === 'function') {
      window.calculateBalance();
    } else {
      // Trigger change event on check-in/check-out fields to recalculate
      const checkinField = document.querySelector('.walkin-check-in');
      const checkoutField = document.querySelector('.walkin-check-out');
      if (checkinField && checkinField.value && checkoutField && checkoutField.value) {
        // Create and dispatch a custom event
        const event = new Event('change', { bubbles: true });
        checkoutField.dispatchEvent(event);
      }
    }
  });

  // Close add-ons popup when clicking outside
  $(document).on("click", function (e) {
    if (!$(e.target).closest('.walkin-addons-dropdown').length) {
      $("#addons-popup").removeClass('show');
    }
  });
});

// Update add-ons summary display
function updateAddonsSummary() {
  const totalAddons = addonsData.bed + addonsData.pillow + addonsData.towel;

  if (totalAddons === 0) {
    $("#addons-summary").text("No add-ons selected");
    $("#addons-details").text("Select add-ons for your stay");
  } else {
    let summary = [];
    if (addonsData.bed > 0) summary.push(`${addonsData.bed} bed${addonsData.bed > 1 ? 's' : ''}`);
    if (addonsData.pillow > 0) summary.push(`${addonsData.pillow} pillow${addonsData.pillow > 1 ? 's' : ''}`);
    if (addonsData.towel > 0) summary.push(`${addonsData.towel} towel${addonsData.towel > 1 ? 's' : ''}`);

    $("#addons-summary").text(summary.join(', '));
    $("#addons-details").text(`${totalAddons} add-on${totalAddons > 1 ? 's' : ''} selected`);
  }
}

// Print receipt function
function printReceipt(data, receiptNumber) {
  // Calculate date and time
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });

  // Calculate days stayed (same-day check-in/check-out = 1 day)
  const checkIn = new Date(data.check_in);
  const checkOut = new Date(data.check_out);
  let daysStayed = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
  if (daysStayed < 1) daysStayed = 1;

  // Room type to price mapping (must match walk-in-modal.html)
  const roomPrices = {
    'Standard': 3500,
    'Family': 4700,
    'Deluxe': 8900
  };

  // Calculate add-on totals first (ensure values are parsed as numbers)
  const bedCount = parseInt(data.add_ons?.bed || 0, 10);
  const pillowCount = parseInt(data.add_ons?.pillow || 0, 10);
  const towelCount = parseInt(data.add_ons?.towel || 0, 10);
  const bedTotal = bedCount * 200;
  const pillowTotal = pillowCount * 50;
  const towelTotal = towelCount * 30;
  const addonTotal = bedTotal + pillowTotal + towelTotal;

  // Use the actual balance from the form (already calculated correctly)
  const total = parseFloat(data.current_balance) || 0;

  // Extract room type from room selection
  const roomSelect = document.querySelector(".walkin-room");
  let roomType = 'Deluxe'; // Default
  let roomPrice = 8900; // Default (Deluxe)

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
  } else if (total > 0 && daysStayed > 0) {
    // Fallback: calculate room price from total if DOM not accessible
    const roomTotal = total - addonTotal;
    const calculatedRoomPrice = roomTotal / daysStayed;

    // Find closest matching room price
    const priceDiff = Object.values(roomPrices).map(p => Math.abs(p - calculatedRoomPrice));
    const minIndex = priceDiff.indexOf(Math.min(...priceDiff));
    roomType = Object.keys(roomPrices)[minIndex];
    roomPrice = roomPrices[roomType];
  }

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
  const triggerPrint = function () {
    try {
      printWindow.print();
      // Return focus to main window after a short delay
      setTimeout(function () {
        window.focus();
        // Close the print window after printing (optional - user can cancel if needed)
        // Uncomment the line below if you want to auto-close after print dialog appears
        // printWindow.close();
      }, 100);
    } catch (e) {
      console.error('Print error:', e);
      window.focus();
    }
  };

  // Wait for content to load, then print
  // Use both onload and a timeout as fallback
  printWindow.onload = function () {
    setTimeout(triggerPrint, 250);
  };

  // Fallback: if onload doesn't fire, try printing after a delay
  setTimeout(function () {
    if (printWindow.document.readyState === 'complete' || printWindow.document.readyState === 'interactive') {
      if (!printWindow.document.body || printWindow.document.body.innerHTML === '') {
        return; // Content not ready yet
      }
      triggerPrint();
    }
  }, 500);

  // Ensure main window regains focus even if print dialog is cancelled
  // Listen for when print window closes or loses focus
  const checkPrintWindow = setInterval(function () {
    if (printWindow.closed) {
      clearInterval(checkPrintWindow);
      window.focus();
    }
  }, 500);

  // Clean up interval after 10 seconds
  setTimeout(function () {
    clearInterval(checkPrintWindow);
    window.focus();
  }, 10000);
}

$(".walkin-book-btn").on("click", function (event) {
  // Prevent submission if button is disabled
  if (this.disabled) {
    event.preventDefault()
    event.stopPropagation()
    return false
  }

  // Check if selected room is under maintenance or in housekeeping
  const selectedRoom = document.querySelector(".walkin-room").value;
  if (selectedRoom) {
    // Get the room element from the front office grid
    const roomElement = document.querySelector(`[data-room="${selectedRoom}"]`);
    if (roomElement) {
      const hasMaintenance = roomElement.classList.contains('maintinance') ||
        roomElement.classList.contains('maintenance') ||
        roomElement.getAttribute('data-housekeeping') === 'under_maintenance';
      const hasHousekeeping = roomElement.classList.contains('housekeeping') ||
        roomElement.getAttribute('data-housekeeping') === 'in_progress';

      console.log('[walkin] Room check:', {
        room: selectedRoom,
        hasMaintenance: hasMaintenance,
        hasHousekeeping: hasHousekeeping,
        classes: roomElement.className,
        dataHousekeeping: roomElement.getAttribute('data-housekeeping')
      });

      if (hasMaintenance) {
        Swal.fire({
          icon: "warning",
          title: "⚠️ Room Under Maintenance",
          html: `
            <div style="text-align: center; padding: 10px;">
              <div style="font-size: 48px; margin-bottom: 15px;">🔧</div>
              <h3 style="color: #d4c21a; font-weight: bold; margin-bottom: 15px;">Room ${selectedRoom} is Under Maintenance</h3>
              <p style="font-size: 16px; color: #333; margin-bottom: 10px;">
                This room is currently unavailable for booking due to maintenance work.
              </p>
              <p style="font-size: 14px; color: #666; margin-top: 10px;">
                Please select a different room to proceed with booking.
              </p>
            </div>
          `,
          confirmButtonText: "OK, I Understand",
          confirmButtonColor: "#d4c21a",
          confirmButtonClass: "swal2-confirm",
          width: 500,
          padding: "2em",
          backdrop: true,
          allowOutsideClick: false,
          allowEscapeKey: true,
          customClass: {
            popup: 'maintenance-error-modal',
            title: 'maintenance-error-title',
            htmlContainer: 'maintenance-error-content'
          }
        });
        return;
      }

      if (hasHousekeeping) {
        Swal.fire({
          icon: "info",
          title: "🧹 Room In Housekeeping",
          html: `
            <div style="text-align: center; padding: 10px;">
              <div style="font-size: 48px; margin-bottom: 15px;">🧹</div>
              <h3 style="color: #0f3f86; font-weight: bold; margin-bottom: 15px;">Room ${selectedRoom} is Currently Being Cleaned</h3>
              <p style="font-size: 16px; color: #333; margin-bottom: 10px;">
                This room is currently in housekeeping and cannot be booked at this time.
              </p>
              <p style="font-size: 14px; color: #666; margin-top: 10px;">
                Please select a different room or wait until housekeeping is complete.
              </p>
            </div>
          `,
          confirmButtonText: "OK, I Understand",
          confirmButtonColor: "#0f3f86",
          confirmButtonClass: "swal2-confirm",
          width: 500,
          padding: "2em",
          backdrop: true,
          allowOutsideClick: false,
          allowEscapeKey: true,
          customClass: {
            popup: 'housekeeping-error-modal',
            title: 'housekeeping-error-title',
            htmlContainer: 'housekeeping-error-content'
          }
        });
        return;
      }
    } else {
      // If room element not found, check via API
      console.log('[walkin] Room element not found, checking via API for room:', selectedRoom);
      // We'll let the backend handle this validation
    }
  }

  // Validate form before submission
  if (window.validateWalkinForm) {
    const validation = window.validateWalkinForm();
    if (!validation.isValid) {
      // Show error message
      Swal.fire({
        icon: "error",
        title: "Validation Error",
        html: `
          <div style="text-align: left; padding: 10px;">
            <p style="margin-bottom: 10px; font-weight: bold;">Please fix the following errors:</p>
            <ul style="margin: 0; padding-left: 20px;">
              ${validation.errors.map(error => `<li style="margin-bottom: 5px;">${error}</li>`).join('')}
            </ul>
          </div>
        `,
        confirmButtonText: "OK",
        confirmButtonColor: "#dc3545",
        width: 500,
        padding: "2em"
      });
      return; // Stop form submission
    }
  }

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
    add_ons: addonsData,
    children_7_years: document.querySelector(".walkin-below-seven").value,
    payment_method: document.querySelector(".walkin-payment-method").value,
    card_number: document.querySelector(".walkin-card-number").value,
    exp_date: document.querySelector(".walkin-card-exp-date").value,
    cvc: document.querySelector(".walkin-card-cvc").value,
    current_balance: (() => {
      const rawValue = document.querySelector(".walkin-balance").value;
      // Simply remove peso symbol and commas
      const cleanValue = rawValue.replace('₱', '').replace(/,/g, '');
      console.log('[DEBUG] Raw balance value:', rawValue);
      console.log('[DEBUG] Clean balance value:', cleanValue);
      return cleanValue;
    })(),
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

          // Calculate days stayed (same-day check-in/check-out = 1 day)
          const checkIn = new Date(data.check_in);
          const checkOut = new Date(data.check_out);
          let daysStayed = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
          if (daysStayed < 1) daysStayed = 1;

          // Room type to price mapping (must match walk-in-modal.html)
          const roomPrices = {
            'Standard': 3500,
            'Family': 4700,
            'Deluxe': 8900
          };

          // Extract room type from room selection
          const roomSelect = document.querySelector(".walkin-room");
          let roomType = 'Deluxe';
          let roomPrice = 8900;

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
          const bedCountPreview = parseInt(data.add_ons?.bed || 0, 10);
          const pillowCountPreview = parseInt(data.add_ons?.pillow || 0, 10);
          const towelCountPreview = parseInt(data.add_ons?.towel || 0, 10);
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
              setTimeout(function () {
                // Get receipt number from response or use default
                const receiptNumber = response.receipt_number || response.reference_number || "00001";
                printReceipt(data, receiptNumber);
              }, 100);
            }
          });
        }
      });
    },
    error: function (xhr, status, error) {
      console.log("Walk-in booking error:", xhr, status, error);

      // Parse error response from backend
      let errorMessage = "Failed to book room. Please try again.";
      let errorDetails = [];

      try {
        if (xhr.responseJSON) {
          // If backend returns JSON with error details
          if (xhr.responseJSON.message) {
            errorMessage = xhr.responseJSON.message;
          }
          if (xhr.responseJSON.errors) {
            errorDetails = Array.isArray(xhr.responseJSON.errors)
              ? xhr.responseJSON.errors
              : Object.values(xhr.responseJSON.errors).flat();
          }
          if (xhr.responseJSON.error) {
            errorMessage = xhr.responseJSON.error;
          }
        } else if (xhr.responseText) {
          // Try to parse response text as JSON
          const response = JSON.parse(xhr.responseText);
          if (response.message) {
            errorMessage = response.message;
          }
          if (response.errors) {
            errorDetails = Array.isArray(response.errors)
              ? response.errors
              : Object.values(response.errors).flat();
          }
        }
      } catch (e) {
        console.log("Error parsing response:", e);
      }

      // Show error modal with details
      let errorHtml = `
        <div style="text-align: left; padding: 10px;">
          <p style="margin-bottom: 10px; font-weight: bold; color: #dc3545;">${errorMessage}</p>
      `;

      if (errorDetails.length > 0) {
        errorHtml += `
          <p style="margin-bottom: 10px; font-weight: 600;">Please fix the following issues:</p>
          <ul style="margin: 0; padding-left: 20px; color: #333;">
            ${errorDetails.map(err => `<li style="margin-bottom: 5px;">${err}</li>`).join('')}
          </ul>
        `;
      } else {
        errorHtml += `
          <p style="color: #666; font-size: 14px;">Please check all required fields and try again.</p>
        `;
      }

      errorHtml += `</div>`;

      Swal.fire({
        icon: "error",
        title: "Booking Failed",
        html: errorHtml,
        confirmButtonText: "OK",
        confirmButtonColor: "#dc3545",
        width: 500,
        padding: "2em"
      });

      // Re-show the modal so user can fix errors
      walkinOverlay.style.display = "flex";

      if (xhr && xhr.responseJSON && xhr.responseJSON.message) {
        errorMessage = xhr.responseJSON.message;
      } else if (xhr && xhr.responseText) {
        try {
          const response = JSON.parse(xhr.responseText);
          if (response.message) {
            errorMessage = response.message;
          } else if (response.error) {
            errorMessage = response.error;
          }
        } catch (e) {
          // If not JSON, use default message
        }
      }

      // Check for specific error messages about maintenance or housekeeping
      if (errorMessage.toLowerCase().includes('maintenance')) {
        Swal.fire({
          icon: "warning",
          title: "⚠️ Room Under Maintenance",
          html: `
            <div style="text-align: center; padding: 10px;">
              <div style="font-size: 48px; margin-bottom: 15px;">🔧</div>
              <h3 style="color: #d4c21a; font-weight: bold; margin-bottom: 15px;">Room Unavailable</h3>
              <p style="font-size: 16px; color: #333; margin-bottom: 10px;">
                ${errorMessage}
              </p>
              <p style="font-size: 14px; color: #666; margin-top: 10px;">
                Please select a different room to proceed with booking.
              </p>
            </div>
          `,
          confirmButtonText: "OK, I Understand",
          confirmButtonColor: "#d4c21a",
          width: 500,
          padding: "2em",
          backdrop: true,
          allowOutsideClick: false,
          allowEscapeKey: true,
        });
      } else if (errorMessage.toLowerCase().includes('housekeeping')) {
        Swal.fire({
          icon: "info",
          title: "🧹 Room In Housekeeping",
          html: `
            <div style="text-align: center; padding: 10px;">
              <div style="font-size: 48px; margin-bottom: 15px;">🧹</div>
              <h3 style="color: #0f3f86; font-weight: bold; margin-bottom: 15px;">Room Unavailable</h3>
              <p style="font-size: 16px; color: #333; margin-bottom: 10px;">
                ${errorMessage}
              </p>
              <p style="font-size: 14px; color: #666; margin-top: 10px;">
                Please select a different room or wait until housekeeping is complete.
              </p>
            </div>
          `,
          confirmButtonText: "OK, I Understand",
          confirmButtonColor: "#0f3f86",
          width: 500,
          padding: "2em",
          backdrop: true,
          allowOutsideClick: false,
          allowEscapeKey: true,
        });
      } else {
        Swal.fire({
          icon: "error",
          title: "Booking Failed",
          text: errorMessage,
          confirmButtonColor: "#1a2d1e",
        });
      }

      // Re-show the modal if it was hidden
      walkinOverlay.style.display = "flex";
    },
  });
});