view = document.getElementById('overview-section')
      const rooms = document.getElementById('rooms-section')
      const viewRoomsBtn = document.getElementById('view-rooms-btn')
    
      function showSection(section) {
        if (section === 'rooms') {
          rooms.style.display = ''
          overview.style.display = 'none'
          tabs.forEach((t) => t.classList.remove('active'))
          document.querySelector('#results-tabs .nav-link[data-target="#rooms-section"]').classList.add('active')
        } else {
          overview.style.display = ''
          rooms.style.display = 'none'
          tabs.forEach((t) => t.classList.remove('active'))
          document.querySelector('#results-tabs .nav-link[data-target="#overview-section"]').classList.add('active')
        }
      }
    
      tabs.forEach((tab) => {
        tab.addEventListener('click', function () {
          const target = this.getAttribute('data-target')
          showSection(target === '#rooms-section' ? 'rooms' : 'overview')
        })
      })
    
      if (viewRoomsBtn) {
        viewRoomsBtn.addEventListener('click', function () {
          showSection('rooms')
        })
      }
    })
    
    // Book room function
    function bookRoom(roomId) {
      // Store room ID for the booking process
      localStorage.setItem('selectedRoomId', roomId)
    
      // Persist selected dates and guest counts from query params
      try {
        const params = new URLSearchParams(window.location.search)
        const checkin = params.get('checkin')
        const checkout = params.get('checkout')
        const rooms = params.get('rooms')
        const adults = params.get('adults')
        const children = params.get('children')
        const stayType = params.get('stayType')
    
        if (checkin) localStorage.setItem('selectedCheckinDate', checkin)
        if (checkout) localStorage.setItem('selectedCheckoutDate', checkout)
        if (rooms) localStorage.setItem('numRooms', rooms)
        if (adults) localStorage.setItem('numAdults', adults)
        if (children) localStorage.setItem('numChildren', children)
        if (stayType) localStorage.setItem('stayType', stayType)
        console.log('[guestbooking/results] saved selection to storage:', {
          roomId,
          checkin,
          checkout,
          rooms,
          adults,
          children,
          stayType
        })
      } catch (e) {
        console.warn('[guestbooking/results] failed to persist selection', e)
      }
    
      // Redirect to book reservation page
      window.location.href = '/guestbooking/book-reservation/'
    }