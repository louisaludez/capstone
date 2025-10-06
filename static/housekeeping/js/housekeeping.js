const popover = document.getElementById('room-popover')
const statusButton = document.querySelectorAll('.status-button')
let selectedRoomNo = null

document.querySelectorAll('.room-box').forEach((box) => {
    box.addEventListener('click', (e) => {
        const rect = box.getBoundingClientRect()
        const containerRect = document.querySelector('.main').getBoundingClientRect()
        const selectedRequest = document.querySelector('.select-request')
        const noBookingMsg = document.getElementById('no-booking-message')
        selectedRoomNo = box.dataset.room
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

        // toggle UI depending on booking availability
        const hasBooking = !box.classList.contains('disabled-room')
        if (noBookingMsg) {
            if (hasBooking) {
                noBookingMsg.classList.add('hidden')
            } else {
                noBookingMsg.classList.remove('hidden')
            }
        }
        document.querySelectorAll('input[name="req"]').forEach((el) => {
            el.disabled = !hasBooking
        })
        document.querySelectorAll('.status-button').forEach((el) => {
            el.disabled = !hasBooking
            el.style.opacity = '1'
            el.style.pointerEvents = hasBooking ? 'auto' : 'none'
        })

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
        let selectedReq = document.querySelector('input[name="req"]:checked')

        if (!selectedReq) {
            // Shake effect
            document.body.classList.add('shake')
            setTimeout(() => document.body.classList.remove('shake'), 500)
            return // Stop here if nothing is selected
        }
        $.ajax({
            type: 'POST',
            url: '/housekeeping/update_status/',
            data: {
                csrfmiddlewaretoken: '{{ csrf_token }}',
                room_no: selectedRoomNo,
                request_type: selectedReq.value,
                status: btn.target.innerText
            },
            success: function (response) {
                // Update room color based on selected status
                const roomEl = document.querySelector(`.room-box[data-room="${selectedRoomNo}"]`)
                if (roomEl) {
                    roomEl.classList.remove('pending', 'progress', 'vacant')
                    const s = btn.target.innerText.toLowerCase()
                    if (s.includes('pending')) roomEl.classList.add('pending')
                    else if (s.includes('progress')) roomEl.classList.add('progress')
                    else roomEl.classList.add('vacant')
                    // ensure booking flag remains true
                    roomEl.setAttribute('data-has-booking', 'true')
                    roomEl.classList.remove('disabled-room')
                }
                Swal.fire({
                    title: 'Success',
                    text: 'Status updated successfully!',
                    icon: 'success',
                    confirmButtonText: 'OK'
                })
            },
            error: function (xhr, status, error) {
                // If server says no active booking today, show green (vacant)
                if (xhr && xhr.status === 404) {
                    const roomEl = document.querySelector(`.room-box[data-room="${selectedRoomNo}"]`)
                    if (roomEl) {
                        roomEl.classList.remove('pending', 'progress')
                        roomEl.classList.add('vacant')
                        roomEl.setAttribute('data-has-booking', 'false')
                        roomEl.classList.add('disabled-room')
                    }
                }
                Swal.fire({
                    title: 'Error',
                    text: xhr && xhr.status === 404 ? 'No booking on this room today.' : 'Failed to update status.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                })
            }
        })
        console.log(btn.target.innerText)
        console.log('Selected request:', selectedReq.value)
    })
})