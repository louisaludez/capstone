document.addEventListener('DOMContentLoaded', function () {
      // Search and filter functionality
      const searchInput = document.getElementById('searchInput')
      const statusFilter = document.getElementById('statusFilter')
      const clearFiltersBtn = document.getElementById('clearFilters')
    
      if (searchInput) {
        searchInput.addEventListener('input', filterReservations)
      }
      if (statusFilter) {
        statusFilter.addEventListener('change', filterReservations)
      }
      if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters)
      }
    
      function filterReservations() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : ''
        const statusValue = statusFilter ? statusFilter.value : ''
        const rows = document.querySelectorAll('tbody tr')
    
        rows.forEach((row) => {
          if (row.querySelector('.text-muted')) return // Skip empty state row
    
          const referenceNo = row.cells[0].textContent.toLowerCase()
          const guestName = row.cells[1].textContent.toLowerCase()
          const service = row.cells[2].textContent.toLowerCase()
          const reservationDate = row.cells[3].textContent.toLowerCase()
          const checkinDate = row.cells[4].textContent.toLowerCase()
          const status = row.cells[6].textContent.trim()
    
          const matchesSearch = !searchTerm || referenceNo.includes(searchTerm) || guestName.includes(searchTerm) || service.includes(searchTerm) || reservationDate.includes(searchTerm) || checkinDate.includes(searchTerm)
          const matchesStatus = !statusValue || status === statusValue
    
          if (matchesSearch && matchesStatus) {
            row.style.display = ''
          } else {
            row.style.display = 'none'
          }
        })
    
        // Show/hide empty state message
        const visibleRows = document.querySelectorAll('tbody tr:not([style*="display: none"])')
        const emptyRow = document.querySelector('tbody tr .text-muted')
        if (emptyRow) {
          if (visibleRows.length === 0) {
            emptyRow.closest('tr').style.display = ''
          } else {
            emptyRow.closest('tr').style.display = 'none'
          }
        }
      }
    
      function clearFilters() {
        if (searchInput) searchInput.value = ''
        if (statusFilter) statusFilter.value = ''
        filterReservations()
      }
    })