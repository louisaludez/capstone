// Form validation and submission
    function proceedToPayment() {
      const form = document.getElementById('guest-form')
      const formData = new FormData(form)
    
      // Basic validation
      const requiredFields = ['firstName', 'lastName', 'email', 'phone']
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
    
      // Email validation
      const email = document.getElementById('email').value
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        alert('Please enter a valid email address.')
        document.getElementById('email').style.borderColor = '#dc3545'
        return
      }
    
      // Phone validation - must be exactly 11 digits
      const phone = document.getElementById('phone').value.replace(/[^0-9]/g, '')
      if (phone.length !== 11) {
        alert('Please enter a valid phone number (11 digits).')
        document.getElementById('phone').style.borderColor = '#dc3545'
        return
      }
    
      // Store guest information in session/localStorage
      const guestInfo = {
        firstName: formData.get('firstName'),
        lastName: formData.get('lastName'),
        country: formData.get('country'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        paymentMethod: document.querySelector('input[name="paymentMethod"]:checked').value
      }
    
      localStorage.setItem('guestInfo', JSON.stringify(guestInfo))
    
      // Redirect to payment page or next step
      window.location.href = '/guestbooking/payment/'
    }
    
    // Phone number validation - only 11 digits
    document.addEventListener('DOMContentLoaded', function () {
      const phoneInput = document.getElementById('phone')
      if (phoneInput) {
        phoneInput.addEventListener('input', function (e) {
          // Only allow digits, max 11
          let value = e.target.value.replace(/[^0-9]/g, '')
          if (value.length > 11) {
            value = value.substring(0, 11)
          }
          e.target.value = value
        })
    
        phoneInput.addEventListener('blur', function () {
          if (this.value.length === 11) {
            this.style.borderColor = '#7eb455'
          } else if (this.value.length > 0 && this.value.length !== 11) {
            this.style.borderColor = '#dc3545'
            alert('Phone number must be exactly 11 digits.')
          } else {
            this.style.borderColor = '#cddcc9'
          }
        })
      }
    
      // Real-time validation for other inputs
      const inputs = document.querySelectorAll('.form-control')
      inputs.forEach((input) => {
        if (input.id !== 'phone') {
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