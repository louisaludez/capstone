 // Card number formatting - only 16 digits
    document.getElementById('cardNumber').addEventListener('input', function (e) {
      let value = e.target.value.replace(/\s/g, '').replace(/[^0-9]/gi, '')
      // Limit to 16 digits
      if (value.length > 16) {
        value = value.substring(0, 16)
      }
      let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value
      e.target.value = formattedValue
    })
    
    // Expiry date formatting
    document.getElementById('expiryDate').addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, '')
      if (value.length >= 2) {
        value = value.substring(0, 2) + '/' + value.substring(2, 4)
      }
      e.target.value = value
    })
    
    // CVC validation (numbers only)
    document.getElementById('cvc').addEventListener('input', function (e) {
      e.target.value = e.target.value.replace(/[^0-9]/g, '')
    })
    
    // Form validation and submission
    function processReservation() {
      const form = document.getElementById('payment-form')
      const formData = new FormData(form)
    
      // Basic validation
      const requiredFields = ['cardHolderName', 'cardNumber', 'cvc', 'expiryDate']
      let isValid = true
    
      requiredFields.forEach((field) => {
        const input = document.getElementById(field)
        if (!input.value.trim()) {
          input.style.borderColor = '#dc3545'
          isValid = false
        } else {
          input.style.borderColor = '#cddcc9'
        }
      })
    
      if (!isValid) {
        alert('Please fill in all required fields.')
        return
      }
    
      // Card number validation - must be exactly 16 digits
      const cardNumber = document.getElementById('cardNumber').value.replace(/\s/g, '')
      if (cardNumber.length !== 16) {
        alert('Please enter a valid credit card number (16 digits).')
        document.getElementById('cardNumber').style.borderColor = '#dc3545'
        return
      }
    
      // CVC validation
      const cvc = document.getElementById('cvc').value
      if (cvc.length < 3 || cvc.length > 4) {
        alert('Please enter a valid CVC/CW.')
        document.getElementById('cvc').style.borderColor = '#dc3545'
        return
      }
    
      // Expiry date validation
      const expiryDate = document.getElementById('expiryDate').value
      if (!/^\d{2}\/\d{2}$/.test(expiryDate)) {
        alert('Please enter a valid expiry date (MM/YY).')
        document.getElementById('expiryDate').style.borderColor = '#dc3545'
        return
      }
    
      // Store payment information
      const paymentInfo = {
        cardHolderName: formData.get('cardHolderName'),
        cardNumber: formData.get('cardNumber'),
        cvc: formData.get('cvc'),
        expiryDate: formData.get('expiryDate'),
        billingAddress: formData.get('cardHolderName'), // Use card holder name as billing address
        paymentMethod: formData.get('paymentMethod')
      }
    
      localStorage.setItem('paymentInfo', JSON.stringify(paymentInfo))
    
      // Save to database and show confirmation modal
      saveReservationToDatabase()
    }
    
    // Save reservation to database
    async function saveReservationToDatabase() {
      try {
        const guestInfo = JSON.parse(localStorage.getItem('guestInfo'))
        const paymentInfo = JSON.parse(localStorage.getItem('paymentInfo'))
        const roomId = localStorage.getItem('selectedRoomId')
        const checkInLS = localStorage.getItem('selectedCheckinDate')
        const checkOutLS = localStorage.getItem('selectedCheckoutDate')
        const numAdults = parseInt(localStorage.getItem('numAdults') || '2', 10)
        const numChildren = parseInt(localStorage.getItem('numChildren') || '0', 10)
    
        const reservationData = {
          guest: guestInfo,
          payment: paymentInfo,
          room_id: roomId,
          check_in_date: checkInLS,
          check_out_date: checkOutLS,
          num_of_adults: numAdults,
          num_of_children: numChildren
        }
    
        const response = await fetch('/guestbooking/save-reservation/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify(reservationData)
        })
    
        if (response.ok) {
          const result = await response.json()
          showConfirmationModal(result)
        } else {
          alert('Error saving reservation. Please try again.')
        }
      } catch (error) {
        console.error('Error:', error)
        alert('Error saving reservation. Please try again.')
      }
    }
    
    // Show confirmation modal with SweetAlert
    function showConfirmationModal(result) {
      Swal.fire({
        title: 'Your reservation has been confirmed!',
        html: `
                                                      <div style="text-align: center; margin: 20px 0;">
                                                       
                                                        <div style="text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                                                          <p style="margin: 5px 0;"><strong>Guest Name:</strong> ${result.guest_name}</p>
                                                          <p style="margin: 5px 0;"><strong>Room no.:</strong> ${result.room_number}</p>
                                                          <p style="margin: 5px 0;"><strong>Reference no.:</strong> ${result.reference_number}</p>
                                                        </div>
                                                      </div>
                                                    `,
        icon: 'success',
        confirmButtonText: 'View Details',
        confirmButtonColor: '#1a2d1a',
    
        customClass: {
          popup: 'swal-wide'
        }
      }).then((result) => {
        if (result.isConfirmed) {
          window.location.href = '/guestbooking/confirmation/'
        } else if (result.dismiss === Swal.DismissReason.cancel) {
          window.location.href = '/assessment/'
        }
      })
    }
    
    // Get CSRF token
    function getCookie(name) {
      let cookieValue = null
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          if (cookie.substring(0, name.length + 1) === name + '=') {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
            break
          }
        }
      }
      return cookieValue
    }
    
    // Real-time validation
    document.addEventListener('DOMContentLoaded', function () {
      const cardNumberInput = document.getElementById('cardNumber')
      if (cardNumberInput) {
        cardNumberInput.addEventListener('blur', function () {
          const cardNumber = this.value.replace(/\s/g, '')
          if (cardNumber.length === 16) {
            this.style.borderColor = '#7eb455'
          } else if (cardNumber.length > 0 && cardNumber.length !== 16) {
            this.style.borderColor = '#dc3545'
          } else {
            this.style.borderColor = '#cddcc9'
          }
        })
      }
    
      const inputs = document.querySelectorAll('.form-control')
      inputs.forEach((input) => {
        if (input.id !== 'cardNumber') {
          input.addEventListener('blur', function () {
            if (this.value.trim()) {
              this.style.borderColor = '#7eb455'
            } else {
              this.style.borderColor = '#cddcc9'
            }
          })
        }
      })
    })