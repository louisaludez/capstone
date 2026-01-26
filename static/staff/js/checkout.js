flatpickr("#co-checkin", { dateFormat: "Y-m-d", allowInput: true });
flatpickr("#co-checkout", { dateFormat: "Y-m-d", allowInput: true });

const pm = document.querySelector(".checkout-payment-method"),
  cf = document.querySelector(".checkout-card-fields");

function toggleCF() {
  if (pm.value === "card") {
    cf.classList.remove("hidden");
    cf.style.height = cf.scrollHeight + "px";
  } else {
    cf.classList.add("hidden");
    cf.style.height = "0px";
  }
}
const checkoutOverlay = document.querySelector(".checkout-overlay");
const checkoutModal = document.querySelector(".checkout-modal");

document
  .getElementById("check-out-modal-btn")
  .addEventListener("click", function () {

    console.log("Checkout button clicked");
    checkoutOverlay.style.display = "flex";

    // Initialize statement button state when modal opens
    setTimeout(function() {
      updateStatementButtonState();
    }, 100);

  });

document.querySelector(".checkout-overlay").addEventListener("click", (e) => {
  if (!document.querySelector(".checkout-modal").contains(e.target)) {
    document.querySelector(".checkout-overlay").style.display = "none";
    closeCheckoutModal();
  }
});

pm.addEventListener("change", toggleCF);


// function startCheckOutTimer(duration, display) {
//   if (checkOutTimerInterval) {
//     clearInterval(checkOutTimerInterval);
//   }
//   let timer = duration - 1,
//     minutes,
//     seconds;
//   checkOutTimerInterval = setInterval(function () {
//     minutes = parseInt(timer / 60, 10);
//     seconds = parseInt(timer % 60, 10);
//     minutes = minutes < 1 ? "" + minutes : minutes;
//     seconds = seconds < 10 ? "0" + seconds : seconds;

//     display.textContent = `${minutes}:${seconds}`;
//     console.log(`Timer: ${minutes}:${seconds}`);
//     if (--timer < 0) {
//       timer = duration;
//       clearInterval(walkInTimerInterval);
//     }
//   }, 1000);
// }

function closeCheckoutModal() {
  checkoutOverlay.style.display = "none";
}


// Function to update statement button state
function updateStatementButtonState() {
  const guestSelect = $(".guests-name-checkout");
  const statementBtn = $("#generate-statement-btn");
  const guestId = guestSelect.val();
  
  console.log("updateStatementButtonState called - guestId:", guestId);
  
  if (statementBtn.length) {
    if (guestId && guestId !== '' && guestId !== null && guestId !== undefined) {
      statementBtn.prop("disabled", false);
      statementBtn.removeAttr("disabled");
      statementBtn.css("opacity", "1");
      statementBtn.css("cursor", "pointer");
      console.log("Statement button ENABLED");
    } else {
      statementBtn.prop("disabled", true);
      statementBtn.attr("disabled", "disabled");
      statementBtn.css("opacity", "0.5");
      statementBtn.css("cursor", "not-allowed");
      console.log("Statement button DISABLED");
    }
  } else {
    console.log("Statement button not found in DOM");
  }
}

$(".guests-name-checkout").on("change", function () {
  console.log("Guest name changed");
  console.log($(this).val());
  var guest_id = $(this).val();
  
  // Enable/disable statement button based on guest selection
  updateStatementButtonState();
  $.ajax({
    url: `/staff/get-guest/${guest_id}/`,
    type: "GET",
    success: function (response) {
      console.log("Gusest data received:", response);
      console.log("Guest Email:", response.email);
      console.log("Guest Address:", response.address);
      console.log("checkin date", response.bookings[0].check_in_date);
      console.log("guest", response.num_of_adults);
      $(".guest-address-checkout").val(response.address);
      $(".guest-email-checkout").val(response.email);
      $(".guest-birth-checkout").val(response.date_of_birth);
      $(".guest-check-in-date-co").val(response.check_in_date);
      $(".guest-check-out-date-co").val(response.check_out_date);
      $(".guest-room-type-checkout").val(response.room);
      $(".total-guest-checkout").val(response.total_of_guests);
      $(".no-adults-checkout").val(response.num_of_adults);
      $(".no-children-checkout").val(response.num_of_children);
      $(".no-below-7-checkout").val(response.no_of_children_below_7);

      function toNumber(value) {
        return parseFloat(value) || 0;
      }

      let billing = toNumber(response.billing);
      let roomService = toNumber(response.room_service_billing);
      let laundry = toNumber(response.laundry_billing);
      let cafe = toNumber(response.cafe_billing);
      let excessPax = toNumber(response.excess_pax_billing);
      let additional = toNumber(response.additional_charge_billing);

      // Check if guest is walk-in and hide room charges if so
      const selectedOption = $(".guests-name-checkout option:selected");
      const bookingSource = selectedOption.attr('data-booking-source') || '';
      const isWalkin = selectedOption.attr('data-is-walkin');
      const roomChargesWrapper = document.querySelector('.checkout-room-charges-wrapper');

      console.log('[checkout.js] bookingSource:', bookingSource, 'isWalkin:', isWalkin);

      // Only hide room charges and additional charges if source is 'walkin'
      const additionalChargesWrapper = document.querySelector('.checkout-additional-charges-wrapper');

      if (bookingSource === 'walkin' && roomChargesWrapper) {
        roomChargesWrapper.style.display = 'none';
        roomChargesWrapper.style.visibility = 'hidden';
        roomChargesWrapper.style.height = '0';
        roomChargesWrapper.style.margin = '0';
        roomChargesWrapper.style.padding = '0';
        console.log('[checkout.js] Hiding Room Charges - guest is walk-in');
        $(".guest-billing-checkout").val(''); // Clear room charges value

        // Also hide Additional Charges for walk-in guests
        if (additionalChargesWrapper) {
          additionalChargesWrapper.style.display = 'none';
          additionalChargesWrapper.style.visibility = 'hidden';
          additionalChargesWrapper.style.height = '0';
          additionalChargesWrapper.style.margin = '0';
          additionalChargesWrapper.style.padding = '0';
          console.log('[checkout.js] Hiding Additional Charges - guest is walk-in');
          $(".guest-additional-charge-checkout").val(''); // Clear additional charges value
        }
      } else if (roomChargesWrapper) {
        roomChargesWrapper.style.display = 'flex';
        roomChargesWrapper.style.visibility = 'visible';
        roomChargesWrapper.style.height = '';
        roomChargesWrapper.style.margin = '';
        roomChargesWrapper.style.padding = '';
        console.log('[checkout.js] Showing Room Charges - guest is from reservation');
        $(".guest-billing-checkout").val(billing);

        // Also show Additional Charges for reservations
        if (additionalChargesWrapper) {
          additionalChargesWrapper.style.display = 'flex';
          additionalChargesWrapper.style.visibility = 'visible';
          additionalChargesWrapper.style.height = '';
          additionalChargesWrapper.style.margin = '';
          additionalChargesWrapper.style.padding = '';
          console.log('[checkout.js] Showing Additional Charges - guest is from reservation');
        }
      } else {
        $(".guest-billing-checkout").val(billing);
      }
      $(".guest-rm-billing-checkout").val(roomService);
      $(".guest-laundry-billing-checkout").val(laundry);
      $(".guest-cafe-billing-checkout").val(cafe);
      $(".guest-ep-billing-checkout").val(excessPax);

      // Only set additional charges if not walk-in
      if (bookingSource !== 'walkin') {
        $(".guest-additional-charge-checkout").val(additional);
      } else {
        $(".guest-additional-charge-checkout").val('');
      }

      // Calculate total - exclude billing (room charges) and additional charges if walk-in
      let total;
      if (bookingSource === 'walkin') {
        // For walk-in: only laundry and cafe (exclude room charges and additional charges)
        total = laundry + cafe;
        console.log('[checkout.js] Walk-in total (excluding room charges and additional charges):', total);
      } else {
        // For reservations or checkin: include all charges including room charges and additional charges
        total = billing + roomService + laundry + cafe + excessPax + additional;
        console.log('[checkout.js] Reservation/Checkin total (including room charges and additional charges):', total);
      }
      $(".guest-total-balance-checkout").val(total.toFixed(2));
    },
    error: function (message) {
      console.error("Error fetching guest data:", message);
    },
  });
});

$(".checkout-submit-btn").on("click", function () {

  console.log("Checkout button clicked");
  $.ajax({
    url: "/staff/api/checkout/",
    type: "POST",
    data: {
      csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),

      guest_id: $(".guests-name-checkout").val(),
      check_in: $(".guest-check-in-date-co").val(),
      check_out: $(".guest-check-out-date-co").val(),
      room: $(".guest-room-type-checkout").val(),

      // Billing Breakdown
      total_billing: $(".guest-billing-checkout").val(),
      room_service: $(".guest-rm-billing-checkout").val(),
      laundry: $(".guest-laundry-billing-checkout").val(),
      cafe: $(".guest-cafe-billing-checkout").val(),
      excess_pax: $(".guest-ep-billing-checkout").val(),
      additional_charges: $(".guest-additional-charge-checkout").val(),

      // Payment info
      payment_method: $(".checkout-payment-method").val(),
      card_number: $(".checkout-card-number").val(),
      card_expiry: $(".checkout-card-exp-date").val(),
      card_cvc: $(".checkout-card-cvc").val(),
      billing_address: $(".checkout-billing-address").val(),
      balance: $(".guest-total-balance-checkout").val(),
    },
    success: function (response) {
      Swal.fire({
        icon: "success",
        title: "Checkout Successful",
        text: response.message || "Guest has been checked out.",
      }).then(function () {
        window.location.reload();
      });
      closeCheckoutModal();


    },
    error: function (xhr) {
      Swal.fire({
        icon: "error",
        title: "Checkout Failed",
        text: xhr.responseText || "Something went wrong.",
      });
    },
  });
});

// Handle Statement of Account button click - open modal with statement preview
$(document).on("click", "#generate-statement-btn", function (e) {
  e.preventDefault();
  e.stopPropagation();
  
  // Check if button is disabled
  if ($(this).prop("disabled")) {
    Swal.fire({
      icon: "warning",
      title: "No Guest Selected",
      text: "Please select a guest first to generate the statement of account.",
    });
    return false;
  }
  
  const guestId = $(".guests-name-checkout").val();
  
  if (!guestId || guestId === '' || guestId === null) {
    Swal.fire({
      icon: "warning",
      title: "No Guest Selected",
      text: "Please select a guest first to generate the statement of account.",
    });
    return false;
  }

  // Store guest ID for use in download button
  $("#statement-modal-overlay").data("guest-id", guestId);
  
  // Show loading state
  $("#statement-loading").show();
  $("#statement-content").hide();
  $("#statement-modal-footer").hide();
  
  // Open the statement modal
  $("#statement-modal-overlay").fadeIn(200);
  
  // Fetch and display the statement HTML via AJAX
  const statementUrl = `/staff/statement-of-account/${guestId}/`;
  
  // Show loading
  $("#statement-loading").show();
  $("#statement-content").hide();
  $("#statement-modal-footer").hide();
  
  // Fetch the statement HTML
  fetch(statementUrl, {
    method: 'GET',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    },
    redirect: 'follow', // Follow redirects
    credentials: 'include' // Include cookies for authentication
  })
    .then(response => {
      console.log('Response status:', response.status);
      console.log('Response URL:', response.url);
      console.log('Requested URL:', statementUrl);
      console.log('Response type:', response.type);
      
      // Check if we were redirected
      const finalUrl = response.url;
      if (finalUrl && !finalUrl.includes('statement-of-account') && finalUrl !== statementUrl) {
        console.error('REDIRECT DETECTED! Expected statement page but got:', finalUrl);
        // Check if it's a JSON error response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return response.json().then(data => {
            throw new Error(data.message || 'Error loading statement');
          });
        }
        throw new Error(`The page was redirected to: ${finalUrl}. This might be due to authentication or permission issues. Please ensure you are logged in with the correct permissions.`);
      }
      
      if (!response.ok) {
        // Check if it's a JSON error response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return response.json().then(data => {
            throw new Error(data.message || `Server error: ${response.status}`);
          });
        }
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }
      
      // Check content type
      const contentType = response.headers.get('content-type');
      console.log('Content-Type:', contentType);
      
      return response.text();
    })
    .then(html => {
      console.log('Fetched HTML length:', html.length);
      console.log('HTML contains "STATEMENT OF ACCOUNT":', html.includes('STATEMENT OF ACCOUNT'));
      console.log('HTML contains "statement-container":', html.includes('statement-container'));
      console.log('HTML preview (first 500 chars):', html.substring(0, 500));
      
      // Check if we got redirected (home page would have different content)
      if ((html.includes('Staff') || html.includes('sidebar')) && !html.includes('STATEMENT OF ACCOUNT') && !html.includes('statement-container')) {
        console.error('Received home page or wrong page instead of statement.');
        console.error('Full HTML (first 2000 chars):', html.substring(0, 2000));
        throw new Error('Received home page instead of statement. The view may have redirected. Please check the console for details.');
      }
      
      // Check if HTML contains the statement content
      if (!html.includes('STATEMENT OF ACCOUNT') && !html.includes('statement-container')) {
        console.error('HTML does not contain statement content.');
        console.error('Full HTML (first 2000 chars):', html.substring(0, 2000));
        throw new Error('The response does not contain statement content. Please check the console for details.');
      }
      
      // Parse the HTML and extract the statement content
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Since the template is standalone, the statement-container should be directly in the body
      let statementContainer = null;
      
      // Method 1: Direct querySelector
      statementContainer = doc.querySelector('.statement-container');
      console.log('Found statement-container via querySelector:', !!statementContainer);
      
      // Method 2: Try body.querySelector
      if (!statementContainer && doc.body) {
        statementContainer = doc.body.querySelector('.statement-container');
        console.log('Found statement-container in body:', !!statementContainer);
      }
      
      // Method 3: Try documentElement.querySelector
      if (!statementContainer) {
        statementContainer = doc.documentElement.querySelector('.statement-container');
        console.log('Found statement-container in documentElement:', !!statementContainer);
      }
      
      // Method 4: If still not found, try to find by text content
      if (!statementContainer) {
        const allDivs = doc.querySelectorAll('div');
        console.log('Total divs found:', allDivs.length);
        for (let div of allDivs) {
          if (div.textContent && div.textContent.includes('STATEMENT OF ACCOUNT')) {
            console.log('Found div with "STATEMENT OF ACCOUNT" text');
            // Check if this div or its parent has statement-container class
            let current = div;
            while (current && current !== doc.body) {
              if (current.classList && current.classList.contains('statement-container')) {
                statementContainer = current;
                console.log('Found statement-container by text search');
                break;
              }
              current = current.parentElement;
            }
            // If not found in parent, check if this div itself has the class
            if (!statementContainer && div.classList && div.classList.contains('statement-container')) {
              statementContainer = div;
              console.log('Found statement-container on the div itself');
            }
            if (statementContainer) break;
          }
        }
      }
      
      // Last resort: extract by regex from HTML string
      if (!statementContainer && html.includes('statement-container')) {
        // More robust regex that handles nested divs
        const startPattern = /<div[^>]*class\s*=\s*["'][^"']*statement-container[^"']*["'][^>]*>/i;
        const startMatch = html.match(startPattern);
        if (startMatch) {
          const startIndex = startMatch.index;
          let depth = 1;
          let endIndex = startIndex + startMatch[0].length;
          
          // Find matching closing div by counting depth
          while (endIndex < html.length && depth > 0) {
            const nextDiv = html.indexOf('<div', endIndex);
            const nextCloseDiv = html.indexOf('</div>', endIndex);
            
            if (nextCloseDiv === -1) break;
            
            if (nextDiv !== -1 && nextDiv < nextCloseDiv) {
              // Check if it's self-closing
              const divEnd = html.indexOf('>', nextDiv);
              if (divEnd !== -1 && html[divEnd - 1] !== '/') {
                depth++;
                endIndex = divEnd + 1;
              } else {
                endIndex = divEnd + 1;
              }
            } else {
              depth--;
              if (depth === 0) {
                endIndex = nextCloseDiv + 6;
                break;
              }
              endIndex = nextCloseDiv + 6;
            }
          }
          
          if (endIndex > startIndex) {
            const containerHtml = html.substring(startIndex, endIndex);
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = containerHtml;
            statementContainer = tempDiv.firstElementChild;
            console.log('Found statement-container via regex extraction');
          }
        }
      }
      
      if (statementContainer) {
        console.log('Successfully found statement-container, inserting into modal');
        // Insert the statement content
        const contentDiv = document.getElementById('statement-content');
        contentDiv.innerHTML = '';
        
        if (statementContainer.cloneNode) {
          contentDiv.appendChild(statementContainer.cloneNode(true));
        } else {
          contentDiv.innerHTML = statementContainer.innerHTML || statementContainer;
        }
        
        // Hide loading, show content and footer
        $("#statement-loading").hide();
        $("#statement-content").show();
        $("#statement-modal-footer").show();
      } else if (html.includes('STATEMENT OF ACCOUNT')) {
        console.log('Found "STATEMENT OF ACCOUNT" text but not container, trying extraction');
        // If we found the text but not the container, try to extract everything between the statement header and end
        const statementStart = html.indexOf('STATEMENT OF ACCOUNT');
        if (statementStart > -1) {
          // Look backwards for the opening div
          const beforeText = html.substring(Math.max(0, statementStart - 1000), statementStart);
          const divStart = beforeText.lastIndexOf('<div');
          if (divStart > -1) {
            const fullStart = Math.max(0, statementStart - 1000) + divStart;
            // Find a reasonable end point (look for closing body or script tags)
            const afterText = html.substring(statementStart);
            const endMarkers = ['</div></div></div>', '</body>', '<script', '</html>'];
            let endIndex = html.length;
            for (let marker of endMarkers) {
              const markerIndex = html.indexOf(marker, statementStart);
              if (markerIndex > -1 && markerIndex < endIndex) {
                endIndex = markerIndex;
              }
            }
            
            if (endIndex > fullStart) {
              const extractedHTML = html.substring(fullStart, endIndex);
              const contentDiv = document.getElementById('statement-content');
              contentDiv.innerHTML = extractedHTML;
              $("#statement-loading").hide();
              $("#statement-content").show();
              $("#statement-modal-footer").show();
              return;
            }
          }
        }
      } else {
        console.warn('Could not find statement-container, trying fallback extraction');
        // Fallback: Since the template is standalone, try to extract the entire body or statement-container div
        if (doc.body) {
          const contentDiv = document.getElementById('statement-content');
          
          // Try to find statement-container in body HTML string
          const bodyHTML = doc.body.innerHTML;
          if (bodyHTML.includes('statement-container')) {
            // Find the statement-container div in the HTML string
            const containerStart = bodyHTML.indexOf('statement-container');
            if (containerStart > -1) {
              // Look backwards for the opening <div> tag
              const beforeContainer = bodyHTML.substring(Math.max(0, containerStart - 300), containerStart);
              const divStart = beforeContainer.lastIndexOf('<div');
              if (divStart > -1) {
                const fullStart = Math.max(0, containerStart - 300) + divStart;
                // Find the matching closing </div> by counting depth
                let depth = 1;
                let endIndex = fullStart + bodyHTML.substring(fullStart).indexOf('>') + 1;
                
                while (endIndex < bodyHTML.length && depth > 0) {
                  const nextDiv = bodyHTML.indexOf('<div', endIndex);
                  const nextCloseDiv = bodyHTML.indexOf('</div>', endIndex);
                  
                  if (nextCloseDiv === -1) break;
                  
                  if (nextDiv !== -1 && nextDiv < nextCloseDiv) {
                    const divEnd = bodyHTML.indexOf('>', nextDiv);
                    if (divEnd !== -1 && bodyHTML[divEnd - 1] !== '/') {
                      depth++;
                      endIndex = divEnd + 1;
                    } else {
                      endIndex = divEnd + 1;
                    }
                  } else {
                    depth--;
                    if (depth === 0) {
                      endIndex = nextCloseDiv + 6;
                      break;
                    }
                    endIndex = nextCloseDiv + 6;
                  }
                }
                
                if (endIndex > fullStart) {
                  const containerHTML = bodyHTML.substring(fullStart, endIndex);
                  const tempDiv = document.createElement('div');
                  tempDiv.innerHTML = containerHTML;
                  const found = tempDiv.querySelector('.statement-container') || tempDiv.firstElementChild;
                  if (found) {
                    contentDiv.innerHTML = '';
                    contentDiv.appendChild(found.cloneNode(true));
                    $("#statement-loading").hide();
                    $("#statement-content").show();
                    $("#statement-modal-footer").show();
                    console.log('Successfully extracted statement-container via fallback');
                    return;
                  }
                }
              }
            }
          }
          
          // Last resort: Since it's a standalone template, show the entire body content
          // But first, try to extract just the statement-container div from the raw HTML
          if (html.includes('<div class="statement-container"')) {
            const startIdx = html.indexOf('<div class="statement-container"');
            let depth = 1;
            let endIdx = html.indexOf('>', startIdx) + 1;
            
            while (endIdx < html.length && depth > 0) {
              const nextDiv = html.indexOf('<div', endIdx);
              const nextClose = html.indexOf('</div>', endIdx);
              if (nextClose === -1) break;
              
              if (nextDiv !== -1 && nextDiv < nextClose) {
                const divEnd = html.indexOf('>', nextDiv);
                if (html[divEnd - 1] !== '/') depth++;
                endIdx = divEnd + 1;
              } else {
                depth--;
                if (depth === 0) {
                  endIdx = nextClose + 6;
                  break;
                }
                endIdx = nextClose + 6;
              }
            }
            
            if (endIdx > startIdx) {
              const extracted = html.substring(startIdx, endIdx);
              contentDiv.innerHTML = extracted;
              $("#statement-loading").hide();
              $("#statement-content").show();
              $("#statement-modal-footer").show();
              console.log('Successfully extracted statement-container from raw HTML');
              return;
            }
          }
          
          // Final fallback: show body content (for standalone template, this should work)
          console.log('Using final fallback: showing entire body content');
          contentDiv.innerHTML = bodyHTML;
          $("#statement-loading").hide();
          $("#statement-content").show();
          $("#statement-modal-footer").show();
        } else {
          console.error('No body found in parsed document');
          throw new Error('Could not extract statement content from response. Please check the console for details.');
        }
      }
    })
    .catch(error => {
      console.error('Error loading statement:', error);
      console.error('Error stack:', error.stack);
      
      let errorMessage = error.message || "Failed to load the statement. Please try again.";
      
      // Provide more helpful error messages
      if (errorMessage.includes('redirected')) {
        errorMessage = "You don't have permission to view this statement, or there was an error. Please check:\n" +
          "1. You are logged in with the correct account\n" +
          "2. The guest ID is valid\n" +
          "3. Check the server console for detailed error messages";
      }
      
      $("#statement-loading").html(`
        <div style="text-align: center; padding: 40px; color: #dc3545;">
          <i class="bi bi-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
          <p style="font-size: 1.1rem; margin: 0; font-weight: 600;">Failed to load statement</p>
          <p style="font-size: 0.9rem; margin-top: 0.5rem; color: #666; white-space: pre-line;">${errorMessage}</p>
          <p style="font-size: 0.8rem; margin-top: 1rem; color: #999;">Please check the browser console and server logs for more details.</p>
        </div>
      `);
      
      Swal.fire({
        icon: "error",
        title: "Error Loading Statement",
        text: errorMessage,
        footer: "Check the browser console (F12) for more details"
      });
    });
  
  return false;
});

// Close statement modal
$(document).on("click", "#statement-modal-close, .statement-modal-overlay", function (e) {
  // Only close if clicking the overlay itself or the close button
  if (e.target === this || $(e.target).is("#statement-modal-close")) {
    $("#statement-modal-overlay").fadeOut(200);
  }
});

// Prevent modal from closing when clicking inside the modal
$(document).on("click", ".statement-modal", function (e) {
  e.stopPropagation();
});

// Handle Download PDF button
$(document).on("click", "#statement-download-btn", function (e) {
  e.preventDefault();
  const guestId = $("#statement-modal-overlay").data("guest-id");
  
  if (!guestId) {
    Swal.fire({
      icon: "error",
      title: "Error",
      text: "Guest ID not found. Please try again.",
    });
    return false;
  }

  // Disable button during download
  const downloadBtn = $(this);
  const originalHtml = downloadBtn.html();
  downloadBtn.prop("disabled", true);
  downloadBtn.html('<i class="bi bi-hourglass-split"></i> Downloading...');
  
  // Download PDF statement
  const statementUrl = `/staff/statement-of-account/${guestId}/pdf/`;
  console.log("Downloading PDF statement:", statementUrl);
  
  // Use fetch API to download PDF without page refresh
  fetch(statementUrl, {
    method: 'GET',
    headers: {
      'Accept': 'application/pdf',
    }
  })
    .then(response => {
      console.log("Response status:", response.status);
      console.log("Response content-type:", response.headers.get('content-type'));
      
      if (!response.ok) {
        return response.text().then(text => {
          throw new Error(`Server error: ${response.status} - ${text}`);
        });
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/pdf')) {
        return response.text().then(text => {
          throw new Error(`Expected PDF but got: ${contentType}. Response: ${text.substring(0, 200)}`);
        });
      }
      
      return response.blob();
    })
    .then(blob => {
      console.log("Blob size:", blob.size, "bytes");
      console.log("Blob type:", blob.type);
      
      if (blob.size === 0) {
        throw new Error('Downloaded file is empty');
      }
      
      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary anchor element and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `Statement_of_Account_${guestId}_${new Date().toISOString().split('T')[0]}.pdf`;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Clean up after a delay
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
      
      console.log("PDF download initiated");
      
      // Show success message
      Swal.fire({
        icon: "success",
        title: "Download Started",
        text: "The statement PDF is being downloaded.",
        timer: 2000,
        showConfirmButton: false
      });
    })
    .catch(error => {
      console.error('Error downloading PDF:', error);
      Swal.fire({
        icon: "error",
        title: "Download Failed",
        text: error.message || "Failed to download PDF. Please try again.",
      });
    })
    .finally(() => {
      // Re-enable button
      downloadBtn.prop("disabled", false);
      downloadBtn.html(originalHtml);
    });
  
  return false;
});

// Initialize statement button state on page load
$(document).ready(function() {
  updateStatementButtonState();
});