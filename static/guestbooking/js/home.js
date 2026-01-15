 // Global variables
    const today = new Date()
    let currentCheckinDate = new Date(today)
    let currentCheckoutDate = new Date(today)
    let selectedCheckin = new Date(today)
    let selectedCheckout = new Date(today)
    selectedCheckout.setDate(selectedCheckout.getDate() + 1) // Tomorrow
    let rooms = 1
    let adults = 2
    let children = 0
    let childAges = []
    let stayType = 'overnight' // Default to overnight stays
    const resultsUrl = "{% url 'guest_booking_results' %}"
    
    // Helpers
    function formatLocalDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
    
    // Initialize the page
    document.addEventListener('DOMContentLoaded', function () {
      updateDateDisplay() // Update date display first
      renderCheckinCalendar()
      renderCheckoutCalendar()
      updateGuestSummary()
      setupEventListeners()
      updateCalendarDisplay() // Set initial calendar display
    })
    
    // Setup all event listeners
    function setupEventListeners() {
      // Stay type toggle
      document.querySelectorAll('.btns').forEach((btn) => {
        btn.addEventListener('click', function () {
          document.querySelectorAll('.btns').forEach((b) => b.classList.remove('active-btn'))
          this.classList.add('active-btn')
    
          // Get stay type and update calendar display
          stayType = this.getAttribute('data-stay-type')
          updateCalendarDisplay()
        })
      })
    
      // Check-in calendar toggle
      document.querySelector('.checkin-calendar').addEventListener('click', function (e) {
        if (!e.target.closest('.calendar-popup')) {
          toggleCheckinCalendar()
        }
      })
    
      // Check-out calendar toggle
      document.querySelector('.checkout-calendar').addEventListener('click', function (e) {
        if (!e.target.closest('.calendar-popup')) {
          toggleCheckoutCalendar()
        }
      })
    
      // Guest toggle
      document.querySelector('.guest-container').addEventListener('click', function (e) {
        if (!e.target.closest('.guest-popup')) {
          toggleGuestPopup()
        }
      })
    
      // Check-in calendar navigation
      document.getElementById('checkin-calendar-popup').addEventListener('click', function (e) {
        if (e.target.closest('button:first-child')) {
          e.preventDefault()
          e.stopPropagation()
          previousCheckinMonth()
        } else if (e.target.closest('button:last-child')) {
          e.preventDefault()
          e.stopPropagation()
          nextCheckinMonth()
        }
      })
    
      // Check-out calendar navigation
      document.getElementById('checkout-calendar-popup').addEventListener('click', function (e) {
        if (e.target.closest('button:first-child')) {
          e.preventDefault()
          e.stopPropagation()
          previousCheckoutMonth()
        } else if (e.target.closest('button:last-child')) {
          e.preventDefault()
          e.stopPropagation()
          nextCheckoutMonth()
        }
      })
    
      // Guest controls
      document.getElementById('guest-popup').addEventListener('click', function (e) {
        if (e.target.closest('#rooms-minus')) {
          e.preventDefault()
          e.stopPropagation()
          changeRooms(-1)
        } else if (e.target.closest('#rooms-plus')) {
          e.preventDefault()
          e.stopPropagation()
          changeRooms(1)
        } else if (e.target.closest('#adults-minus')) {
          e.preventDefault()
          e.stopPropagation()
          changeAdults(-1)
        } else if (e.target.closest('#adults-plus')) {
          e.preventDefault()
          e.stopPropagation()
          changeAdults(1)
        } else if (e.target.closest('#children-minus')) {
          e.preventDefault()
          e.stopPropagation()
          changeChildren(-1)
        } else if (e.target.closest('#children-plus')) {
          e.preventDefault()
          e.stopPropagation()
          changeChildren(1)
        }
      })
    
      // Search button
      document.getElementById('search-btn').addEventListener('click', searchRooms)
    
      // Close popups when clicking outside
      document.addEventListener('click', function (event) {
        const checkinCalendarPopup = document.getElementById('checkin-calendar-popup')
        const checkoutCalendarPopup = document.getElementById('checkout-calendar-popup')
        const guestPopup = document.getElementById('guest-popup')
        const checkinCalendarContainer = document.querySelector('.checkin-calendar')
        const checkoutCalendarContainer = document.querySelector('.checkout-calendar')
        const guestContainer = document.querySelector('.guest-container')
    
        // Check if click is inside check-in calendar popup or its container
        const isCheckinCalendarClick = checkinCalendarContainer.contains(event.target) || checkinCalendarPopup.contains(event.target)
    
        // Check if click is inside check-out calendar popup or its container
        const isCheckoutCalendarClick = checkoutCalendarContainer.contains(event.target) || checkoutCalendarPopup.contains(event.target)
    
        // Check if click is inside guest popup or its container
        const isGuestClick = guestContainer.contains(event.target) || guestPopup.contains(event.target)
    
        // Close check-in calendar popup if click is outside
        if (!isCheckinCalendarClick) {
          checkinCalendarPopup.classList.remove('show')
        }
    
        // Close check-out calendar popup if click is outside
        if (!isCheckoutCalendarClick) {
          checkoutCalendarPopup.classList.remove('show')
        }
    
        // Close guest popup if click is outside
        if (!isGuestClick) {
          guestPopup.classList.remove('show')
        }
      })
    }
    
    // Update calendar display based on stay type
    function updateCalendarDisplay() {
      const calendarContainer = document.querySelector('.calendars')
    
      if (stayType === 'overnight') {
        // For overnight stays, show both calendars (check-in and check-out)
        calendarContainer.classList.remove('overnight-mode')
        // Ensure checkout is at least one day after checkin
        if (selectedCheckout <= selectedCheckin) {
          selectedCheckout = new Date(selectedCheckin)
          selectedCheckout.setDate(selectedCheckout.getDate() + 1)
          updateDateDisplay()
        }
      } else {
        // For day use stays, hide check-out calendar and center check-in
        calendarContainer.classList.add('overnight-mode')
        // Set checkout to same as checkin for day use stays
        selectedCheckout = new Date(selectedCheckin)
        updateDateDisplay()
      }
    
      // Re-render calendars to reflect changes
      renderCheckinCalendar()
      renderCheckoutCalendar()
    }
    
    // Calendar functions
    function toggleCheckinCalendar() {
      const popup = document.getElementById('checkin-calendar-popup')
      popup.classList.toggle('show')
    
      // Close other popups if open
      document.getElementById('checkout-calendar-popup').classList.remove('show')
      document.getElementById('guest-popup').classList.remove('show')
    }
    
    function toggleCheckoutCalendar() {
      const popup = document.getElementById('checkout-calendar-popup')
      popup.classList.toggle('show')
    
      // Close other popups if open
      document.getElementById('checkin-calendar-popup').classList.remove('show')
      document.getElementById('guest-popup').classList.remove('show')
    }
    
    function renderCheckinCalendar() {
      const month = currentCheckinDate.getMonth()
      const year = currentCheckinDate.getFullYear()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      const startDate = new Date(firstDay)
      startDate.setDate(startDate.getDate() - firstDay.getDay() + 1)
    
      const calendarDays = document.getElementById('checkin-calendar-days')
      const monthDisplay = document.getElementById('checkin-calendar-month')
    
      monthDisplay.textContent = new Date(year, month).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    
      calendarDays.innerHTML = ''
    
      for (let i = 0; i < 42; i++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + i)
    
        const dayElement = document.createElement('div')
        dayElement.className = 'calendar-day'
        dayElement.textContent = date.getDate()
    
        if (date.getMonth() !== month) {
          dayElement.classList.add('disabled')
        } else {
          dayElement.addEventListener('click', function (e) {
            e.preventDefault()
            e.stopPropagation()
            selectCheckinDate(date)
          })
    
          if (date.getTime() === selectedCheckin.getTime()) {
            dayElement.classList.add('selected')
          } else if (date > selectedCheckin && date < selectedCheckout) {
            dayElement.classList.add('range')
          }
        }
    
        calendarDays.appendChild(dayElement)
      }
    }
    
    function renderCheckoutCalendar() {
      const month = currentCheckoutDate.getMonth()
      const year = currentCheckoutDate.getFullYear()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      const startDate = new Date(firstDay)
      startDate.setDate(startDate.getDate() - firstDay.getDay() + 1)
    
      const calendarDays = document.getElementById('checkout-calendar-days')
      const monthDisplay = document.getElementById('checkout-calendar-month')
    
      monthDisplay.textContent = new Date(year, month).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    
      calendarDays.innerHTML = ''
    
      for (let i = 0; i < 42; i++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + i)
    
        const dayElement = document.createElement('div')
        dayElement.className = 'calendar-day'
        dayElement.textContent = date.getDate()
    
        if (date.getMonth() !== month) {
          dayElement.classList.add('disabled')
        } else {
          dayElement.addEventListener('click', function (e) {
            e.preventDefault()
            e.stopPropagation()
            selectCheckoutDate(date)
          })
    
          if (date.getTime() === selectedCheckout.getTime()) {
            dayElement.classList.add('selected')
          } else if (date > selectedCheckin && date < selectedCheckout) {
            dayElement.classList.add('range')
          }
        }
    
        calendarDays.appendChild(dayElement)
      }
    }
    
    function selectCheckinDate(date) {
      selectedCheckin = new Date(date)
    
      if (stayType === 'overnight') {
        // For overnight stays, ensure checkout is at least one day after checkin
        if (selectedCheckout <= selectedCheckin) {
          selectedCheckout = new Date(date)
          selectedCheckout.setDate(selectedCheckout.getDate() + 1)
        }
      } else {
        // For day use stays, checkout is same as checkin
        selectedCheckout = new Date(date)
      }
    
      updateDateDisplay()
      renderCheckinCalendar()
      renderCheckoutCalendar()
    }
    
    function selectCheckoutDate(date) {
      // For day use stays, checkout selection is disabled
      if (stayType === 'dayuse') {
        return
      }
    
      if (date > selectedCheckin) {
        selectedCheckout = new Date(date)
        updateDateDisplay()
        renderCheckinCalendar()
        renderCheckoutCalendar()
      }
    }
    
    function updateDateDisplay() {
      document.getElementById('checkin-date').textContent = selectedCheckin.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
      document.getElementById('checkout-date').textContent = selectedCheckout.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
      document.getElementById('checkin-day').textContent = selectedCheckin.toLocaleDateString('en-US', { weekday: 'long' })
      document.getElementById('checkout-day').textContent = selectedCheckout.toLocaleDateString('en-US', { weekday: 'long' })
    }
    
    function previousCheckinMonth() {
      currentCheckinDate.setMonth(currentCheckinDate.getMonth() - 1)
      renderCheckinCalendar()
    }
    
    function nextCheckinMonth() {
      currentCheckinDate.setMonth(currentCheckinDate.getMonth() + 1)
      renderCheckinCalendar()
    }
    
    function previousCheckoutMonth() {
      currentCheckoutDate.setMonth(currentCheckoutDate.getMonth() - 1)
      renderCheckoutCalendar()
    }
    
    function nextCheckoutMonth() {
      currentCheckoutDate.setMonth(currentCheckoutDate.getMonth() + 1)
      renderCheckoutCalendar()
    }
    
    // Guest functions
    function toggleGuestPopup() {
      const popup = document.getElementById('guest-popup')
      popup.classList.toggle('show')
    
      // Close calendar popups if open
      document.getElementById('checkin-calendar-popup').classList.remove('show')
      document.getElementById('checkout-calendar-popup').classList.remove('show')
    }
    
    function changeRooms(delta) {
      rooms = Math.max(1, Math.min(10, rooms + delta))
      document.getElementById('rooms-count').textContent = rooms
      updateGuestSummary()
    }
    
    function changeAdults(delta) {
      adults = Math.max(1, Math.min(20, adults + delta))
      document.getElementById('adults-count').textContent = adults
      updateGuestSummary()
    }
    
    function changeChildren(delta) {
      children = Math.max(0, Math.min(10, children + delta))
      document.getElementById('children-count').textContent = children
    
      if (children > 0) {
        document.getElementById('children-ages').style.display = 'block'
        renderChildAges()
      } else {
        document.getElementById('children-ages').style.display = 'none'
      }
    
      updateGuestSummary()
    }
    
    function renderChildAges() {
      const container = document.getElementById('children-ages')
      container.innerHTML = ''
    
      for (let i = 0; i < children; i++) {
        if (!childAges[i]) childAges[i] = 1
    
        const select = document.createElement('select')
        select.className = 'child-age-select'
        select.innerHTML = '<option value="">Age of Child ' + (i + 1) + '</option>'
    
        for (let age = 0; age <= 17; age++) {
          const option = document.createElement('option')
          option.value = age
          option.textContent = age === 1 ? '1 year old' : age + ' years old'
          option.selected = childAges[i] === age
          select.appendChild(option)
        }
    
        select.addEventListener('change', function (e) {
          childAges[i] = parseInt(e.target.value)
        })
    
        container.appendChild(select)
      }
    }
    
    function updateGuestSummary() {
      let summary = adults + ' Adult' + (adults > 1 ? 's' : '')
      if (children > 0) {
        summary += ', ' + children + ' Child' + (children > 1 ? 'ren' : '')
      }
      document.getElementById('guest-summary').textContent = summary
      document.getElementById('room-summary').textContent = rooms + ' room' + (rooms > 1 ? 's' : '')
    }
    
    // Search function
    function searchRooms() {
      const searchData = {
        checkin: selectedCheckin,
        checkout: selectedCheckout,
        rooms: rooms,
        adults: adults,
        children: children,
        childAges: childAges
      }
    
      console.log('Searching with data:', searchData)
    
      // Build query params and navigate to results page (use LOCAL date, avoid UTC shift)
      const toLocal = (d) => formatLocalDate(new Date(d))
      const params = new URLSearchParams({
        stayType: stayType,
        checkin: toLocal(selectedCheckin),
        checkout: toLocal(selectedCheckout),
        rooms: String(rooms),
        adults: String(adults),
        children: String(children),
        childAges: childAges.filter((age) => age !== undefined).join(',')
      })
    
      const updatedUrl = `${resultsUrl}?${params.toString()}`
      console.log('Navigating to URL:', updatedUrl)
    
      window.location.href = updatedUrl
    }