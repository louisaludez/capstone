const popover = document.getElementById('room-popover')
const statusButton = document.querySelectorAll('.status-button')
let selectedRoomNo = null

document.querySelectorAll('.room-box').forEach((box) => {
    box.addEventListener('click', (e) => {
        const rect = box.getBoundingClientRect()
        const containerRect = document.querySelector('.main').getBoundingClientRect()
        const selectedRequest = document.querySelector('.select-request')
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
                Swal.fire({
                    title: 'Success',
                    text: 'Status updated successfully!',
                    icon: 'success',
                    confirmButtonText: 'OK'
                })
            },
            error: function (xhr, status, error) {
                Swal.fire({
                    title: 'Error',
                    text: 'Failed to update status.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                })
            }
        })
        console.log(btn.target.innerText)
        console.log('Selected request:', selectedReq.value)
    })
})