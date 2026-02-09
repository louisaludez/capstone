const popover = document.getElementById('room-popover')
const statusButton = document.querySelectorAll('.status-button')
let selectedRoomNo = null

document.querySelectorAll('.room-box').forEach((box) => {
    box.addEventListener('click', (e) => {
        console.log('=== ROOM CLICKED ===')
        const rect = box.getBoundingClientRect()
        const containerRect = document.querySelector('.main').getBoundingClientRect()
        const selectedRequest = document.querySelector('.select-request')
        const noBookingMsg = document.getElementById('no-booking-message')
        selectedRoomNo = box.dataset.room
        console.log('Selected room number:', selectedRoomNo)
        console.log('Room element:', box)
        console.log('Room data-has-booking:', box.getAttribute('data-has-booking'))
        selectedRequest.textContent = `Select Request for room : ${selectedRoomNo}`
        // Show popover offscreen temporarily to measure it
        popover.style.visibility = 'hidden'
        popover.classList.remove('hidden')
        popover.style.left = '-9999px'
        popover.style.top = '-9999px'

        const popoverRect = popover.getBoundingClientRect()

        let left = rect.right + window.scrollX + 10
        let arrowSide = 'left' // default

        if (left + popoverRect.width > containerRect.right) {
            left = rect.left + window.scrollX - popoverRect.width - 10
            arrowSide = 'right'
        }

        popover.style.left = `${left}px`
        popover.style.top = `${rect.top + window.scrollY}px`

        // toggle arrow classes
        popover.classList.remove('arrow-left', 'arrow-right')
        popover.classList.add(`arrow-${arrowSide}`)

        // Check if there's a checked-in guest
        const hasBooking = box.getAttribute('data-has-booking') === 'true'
        console.log('Has booking (checked-in guest):', hasBooking)
        if (noBookingMsg) {
            if (hasBooking) {
                noBookingMsg.classList.add('hidden')
            } else {
                noBookingMsg.classList.remove('hidden')
            }
        }
        // Enable all inputs regardless of booking status
        document.querySelectorAll('input[name="request_types"]').forEach((el) => {
            el.disabled = false
        })
        // Enable/disable status buttons based on booking status
        console.log('=== PROCESSING STATUS BUTTONS ===')
        document.querySelectorAll('.status-button').forEach((el, index) => {
            const buttonText = el.innerText.toLowerCase().trim()
            const isUnderMaintenance = buttonText.includes('maintenance') || buttonText.includes('under maintenance')
            console.log(`Button ${index}: "${el.innerText}" -> isUnderMaintenance: ${isUnderMaintenance}, hasBooking: ${hasBooking}`)

            if (isUnderMaintenance && hasBooking) {
                // Disable under-maintenance button if guest is checked in
                el.disabled = true
                el.style.opacity = '0.5'
                el.style.cursor = 'not-allowed'
                el.title = 'Cannot set Under Maintenance when guest is checked in'
                console.log('✓ Under Maintenance button DISABLED (room has guest)')
            } else {
                el.disabled = false
                el.style.opacity = '1'
                el.style.cursor = 'pointer'
                el.title = ''
                if (isUnderMaintenance) {
                    console.log('✓ Under Maintenance button ENABLED (room has no guest)')
                }
            }
            console.log(`  Final state - disabled: ${el.disabled}, opacity: ${el.style.opacity}`)
        })
        console.log('=== END PROCESSING STATUS BUTTONS ===')

        // finally show it for real
        popover.style.visibility = 'visible'
    })
})

// Hide popover if clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.room-box') && !e.target.closest('#room-popover')) {
        popover.classList.add('hidden')
    }
})
statusButton.forEach((button) => {
    button.addEventListener('click', (btn) => {
        console.log('=== STATUS BUTTON CLICKED ===')
        console.log('Button clicked:', btn.target.innerText)
        console.log('Button disabled state:', btn.target.disabled)
        console.log('Selected room:', selectedRoomNo)

        const buttonText = btn.target.innerText.toLowerCase().trim()
        const isUnderMaintenance = buttonText.includes('maintenance') || buttonText.includes('under maintenance')
        console.log('Is Under Maintenance button:', isUnderMaintenance)

        // Check if button is disabled
        if (btn.target.disabled) {
            console.log('⚠️ Button is DISABLED - showing warning')
            // Show error message for disabled button
            if (isUnderMaintenance) {
                Swal.fire({
                    title: 'Cannot Update Status',
                    text: 'Cannot set room to Under Maintenance when there is a checked-in guest.',
                    icon: 'warning',
                    confirmButtonText: 'OK'
                })
            }
            return // Stop here if button is disabled
        }

        const checkedInputs = document.querySelectorAll('input[name="request_types"]:checked')
        const requestTypes = Array.from(checkedInputs).map((el) => el.value)
        console.log('Selected requests:', requestTypes.length ? requestTypes : 'NONE')

        // For "Under Maintenance" and "No requests", request type is not required
        // For other statuses, at least one request type is required
        if (!isUnderMaintenance && !buttonText.includes('no requests')) {
            if (requestTypes.length === 0) {
                console.log('⚠️ No request selected - showing shake effect')
                document.body.classList.add('shake')
                setTimeout(() => document.body.classList.remove('shake'), 500)
                return
            }
        }

        // For Under Maintenance and No requests we send a single placeholder; backend will use it for the one record
        const typesToSend = requestTypes.length > 0 ? requestTypes : ['Room Status Update']

        console.log('✓ Proceeding with AJAX request')
        console.log('Request data:', {
            room_no: selectedRoomNo,
            request_types: typesToSend,
            status: btn.target.innerText
        })

        $.ajax({
            type: 'POST',
            url: '/housekeeping/update_status/',
            traditional: true,
            data: {
                csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value || '',
                room_no: selectedRoomNo,
                request_types: typesToSend,
                status: btn.target.innerText
            },
            success: function (response) {
                console.log('=== AJAX SUCCESS ===')
                console.log('Response:', response)
                console.log('Response type:', typeof response)

                // Handle both string and object responses
                let responseData = response
                if (typeof response === 'string') {
                    try {
                        responseData = JSON.parse(response)
                        console.log('Parsed response:', responseData)
                    } catch (e) {
                        console.log('Response is not JSON, using as-is')
                    }
                }

                // Update room color based on selected status
                const roomEl = document.querySelector(`.room-box[data-room="${selectedRoomNo}"]`)
                console.log('Room element found:', roomEl)

                if (roomEl) {
                    roomEl.classList.remove('pending', 'progress', 'vacant', 'maintenance')
                    const s = btn.target.innerText.toLowerCase()
                    console.log('Status text:', s)

                    if (s.includes('pending')) {
                        roomEl.classList.add('pending')
                        console.log('✓ Added pending class')
                    } else if (s.includes('progress')) {
                        roomEl.classList.add('progress')
                        console.log('✓ Added progress class')
                    } else if (s.includes('maintenance')) {
                        roomEl.classList.add('maintenance')
                        console.log('✓ Added maintenance class')
                    } else {
                        roomEl.classList.add('vacant')
                        console.log('✓ Added vacant class')
                    }

                    // Only update booking flag if response indicates there's a guest
                    // Otherwise keep the current value (false if no guest)
                    if (responseData && responseData.has_guest !== undefined) {
                        const newBookingState = responseData.has_guest ? 'true' : 'false'
                        roomEl.setAttribute('data-has-booking', newBookingState)
                        console.log('✓ Updated data-has-booking to:', newBookingState)
                    } else {
                        console.log('⚠️ Response does not have has_guest field')
                    }

                    console.log('Final room classes:', roomEl.className)
                    console.log('Final data-has-booking:', roomEl.getAttribute('data-has-booking'))
                } else {
                    console.error('❌ Room element not found!')
                }

                Swal.fire({
                    title: 'Success',
                    text: 'Status updated successfully!',
                    icon: 'success',
                    confirmButtonText: 'OK'
                })
                console.log('=== END AJAX SUCCESS ===')
            },
            error: function (xhr, status, error) {
                console.error('AJAX error:', xhr, status, error)
                let errorMessage = 'Failed to update status.'

                if (xhr && xhr.status === 400) {
                    // Handle case when trying to set under-maintenance with checked-in guest
                    try {
                        const response = JSON.parse(xhr.responseText)
                        if (response.error) {
                            errorMessage = response.error
                        }
                    } catch (e) {
                        console.error('Error parsing response:', e)
                        errorMessage = 'Cannot set room to Under Maintenance when there is a checked-in guest.'
                    }
                } else if (xhr && xhr.status === 404) {
                    // If server says no active booking today, show green (vacant)
                    const roomEl = document.querySelector(`.room-box[data-room="${selectedRoomNo}"]`)
                    if (roomEl) {
                        roomEl.classList.remove('pending', 'progress', 'maintenance')
                        roomEl.classList.add('vacant')
                        roomEl.setAttribute('data-has-booking', 'false')
                    }
                    errorMessage = 'No booking on this room today.'
                } else {
                    // Other errors - log for debugging
                    console.error('Unexpected error status:', xhr ? xhr.status : 'unknown')
                    if (xhr && xhr.responseText) {
                        try {
                            const response = JSON.parse(xhr.responseText)
                            if (response.error) {
                                errorMessage = response.error
                            }
                        } catch (e) {
                            console.error('Could not parse error response:', e)
                        }
                    }
                }

                Swal.fire({
                    title: 'Error',
                    text: errorMessage,
                    icon: 'error',
                    confirmButtonText: 'OK'
                })
            }
        })
        console.log(btn.target.innerText)
        console.log('Selected requests:', requestTypes)
    })
})