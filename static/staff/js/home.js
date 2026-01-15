// Front office log date selector with green-themed calendar
    flatpickr('#date-select', {
      dateFormat: 'Y-m-d',
      disableMobile: true,
      monthSelectorType: 'dropdown',
      locale: { firstDayOfWeek: 1 }, // Monday first
      defaultDate: new Date(),
      onChange: function (selectedDates, dateStr) {
        if (dateStr) {
          // Refresh rooms when date changes
          try {
            refreshRooms(dateStr)
          } catch (e) {
            console.warn('refreshRooms not ready yet')
          }
        }
      }
    })
    
    flatpickr('#calendar', {
      dateFormat: 'Y-m-d',
      disableMobile: true, // Forces desktop-style calendar on mobile
      monthSelectorType: 'dropdown',
      locale: { firstDayOfWeek: 1 }
    })
    flatpickr('#check-in', {
      dateFormat: 'Y-m-d',
      disableMobile: true,
      monthSelectorType: 'dropdown',
      locale: { firstDayOfWeek: 1 }
    })
    flatpickr('#check-out', {
      dateFormat: 'Y-m-d',
      disableMobile: true,
      monthSelectorType: 'dropdown',
      locale: { firstDayOfWeek: 1 }
    })
  </script>
  <script>
    $(function () {
      const $date = $('#date-select')
    
      // Add loading state function
      function showLoading() {
        $('.room-information .cont div[id$="-count"]').each(function () {
          $(this).addClass('loading').text('...')
        })
        $('.rooms-occupied .ro-count').each(function () {
          $(this).addClass('loading').text('...')
        })
      }
    
      // Remove loading state function
      function hideLoading() {
        $('.room-information .cont div[id$="-count"], .rooms-occupied .ro-count').removeClass('loading')
      }
    
      function refreshRooms(date) {
        if (!date) return
    
        // Show loading state
        showLoading()
    
        $.getJSON('/staff/api/room-status/', { date })
          .done(function (data) {
            console.log('🔍 room‑status:', data)
    
            // Hide loading state
            hideLoading()
    
            // Clear all status classes first (we'll reapply them based on data)
            $('[data-room]').each(function () {
              $(this).removeClass('occupied vacant reserved housekeeping maintinance available')
            })
    
            // Apply housekeeping status first (takes priority for color)
            if (data.housekeeping_status) {
              console.log('🔍 Housekeeping status data:', data.housekeeping_status)
              Object.keys(data.housekeeping_status).forEach(function (roomCode) {
                const $r = $(`[data-room="${roomCode}"]`)
                const hkStatus = data.housekeeping_status[roomCode]
                console.log(`Room ${roomCode}: housekeeping status = "${hkStatus}"`)
                if ($r.length) {
                  // Remove all status classes first
                  $r.removeClass('housekeeping-box under_maintinance-box housekeeping maintinance occupied vacant reserved')
                  // Add appropriate housekeeping class
                  if (hkStatus === 'in_progress') {
                    $r.addClass('housekeeping')
                    $r.removeClass('vacant')
                    $r.attr('data-housekeeping', 'in_progress')
                    console.log(`  ✓ Added 'housekeeping' class to room ${roomCode}`)
                  } else if (hkStatus === 'under_maintenance') {
                    // Remove all status classes including 'available' which might be set from server
                    $r.removeClass('vacant occupied reserved housekeeping available maintinance')
                    $r.addClass('maintinance')
                    // Set inline style to override any conflicting classes
                    $r.css('background-color', '#d4c21a')
                    $r.attr('data-housekeeping', 'under_maintenance')
                    console.log(`  ✓ Added 'maintinance' class to room ${roomCode}`)
                    console.log(`  ✓ Removed 'available' class`)
                    console.log(`  ✓ Room ${roomCode} classes after:`, $r.attr('class'))
                    console.log(`  ✓ Room ${roomCode} computed background:`, window.getComputedStyle($r[0]).backgroundColor)
                  } else if (hkStatus === 'pending') {
                    $r.attr('data-housekeeping', 'pending')
                    console.log(`  ✓ Set pending status for room ${roomCode}`)
                  }
                } else {
                  console.warn(`❌ Room element not found for room code: ${roomCode}`)
                }
              })
            } else {
              console.log('⚠️ No housekeeping_status in response')
            }
    
            // Mark occupied (but housekeeping in_progress will show blue, maintenance will show yellow)
            ;(data.occupied || []).forEach(function (roomCode) {
              const $r = $(`[data-room="${roomCode}"]`)
              if ($r.length) {
                // Only add occupied class if not in housekeeping or maintenance
                const hkStatus = data.housekeeping_status && data.housekeeping_status[roomCode]
                if (hkStatus !== 'in_progress' && hkStatus !== 'under_maintenance') {
                  // Only add occupied if not already in maintenance or housekeeping
                  if (!$r.hasClass('maintinance') && !$r.hasClass('housekeeping')) {
                    $r.removeClass('vacant').addClass('occupied')
                  }
                }
                // Tooltip with guest and checkout
                const d = (data.occupied_details && data.occupied_details[roomCode]) || null
                if (d) {
                  $r.attr('title', `${d.guest} — out ${d.check_out}`)
                  $r.attr('data-tooltip', `${d.guest} — out ${d.check_out}`)
                } else {
                  $r.removeAttr('title data-tooltip')
                }
              } else {
                console.warn('Missing room div for:', roomCode)
              }
            })
    
            // Mark reserved (but not overriding occupied, housekeeping, or maintenance)
            ;(data.reserved || []).forEach(function (roomCode) {
              const $r = $(`[data-room="${roomCode}"]`)
              if ($r.length && !$r.hasClass('occupied') && !$r.hasClass('housekeeping') && !$r.hasClass('maintinance')) {
                $r.removeClass('vacant').addClass('reserved')
                const d = (data.reserved_details && data.reserved_details[roomCode]) || null
                if (d) {
                  $r.attr('title', `${d.guest} — out ${d.check_out}`)
                  $r.attr('data-tooltip', `${d.guest} — out ${d.check_out}`)
                } else {
                  $r.removeAttr('title data-tooltip')
                }
              }
            })
    
            // Ensure all rooms have at least a 'vacant' class if they don't have any status
            $('[data-room]').each(function () {
              const $r = $(this)
              // Check if room has any status class
              if (!$r.hasClass('occupied') && !$r.hasClass('reserved') && !$r.hasClass('housekeeping') && !$r.hasClass('maintinance') && !$r.hasClass('vacant')) {
                // No status class found, add vacant as default
                $r.addClass('vacant')
                console.log(`  → Room ${$r.attr('data-room')} had no status class, added 'vacant'`)
              }
            })
    
            // Update Room Information section
            if (data.room_info) {
              $('#vacant-count').text(data.room_info.vacant)
              $('#occupied-count').text(data.room_info.occupied)
              $('#maintenance-count').text(data.room_info.maintenance)
              $('#housekeeping-count').text(data.room_info.housekeeping)
              $('#reserved-count').text(data.room_info.reserved)
              $('#total-count').text(data.room_info.total)
            }
    
            // Update Rooms Occupied section
            if (data.rooms_occupied) {
              $('#deluxe-count').text(data.rooms_occupied.deluxe)
              $('#family-count').text(data.rooms_occupied.family)
              $('#standard-count').text(data.rooms_occupied.standard)
            }
          })
          .fail(function (xhr) {
            console.error('Error loading room status:', xhr.responseText)
            hideLoading()
    
            // Show error state
            $('.room-information .cont div[id$="-count"], .rooms-occupied .ro-count').text('Error')
          })
      }
    
      // on change
      $date.on('change', function () {
        refreshRooms(this.value)
      })
    
      // default to today
      const today = new Date().toISOString().slice(0, 10)
      $date.val(today).trigger('change')
    })