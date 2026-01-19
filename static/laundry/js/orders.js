
$(document).ready(function () {
  console.log('Laundry orders page loaded');

  // Initialize pagination data on page load
  initializePagination();

  // Select all functionality
  $(document).on('change', 'input[type="checkbox"]:first', function () {
    const isChecked = $(this).is(':checked');
    console.log('Select all checkbox changed:', isChecked);

    // Check/uncheck all order checkboxes
    $('.order-checkbox').prop('checked', isChecked);

    // Update select all checkbox state
    updateSelectAllState();
  });

  // Individual checkbox functionality
  $(document).on('change', '.order-checkbox', function () {
    console.log('Individual checkbox changed');
    updateSelectAllState();
  });

  function initializePagination() {
    // Get the current page from the URL or default to 1
    const urlParams = new URLSearchParams(window.location.search);
    const currentPage = parseInt(urlParams.get('page')) || 1;

    // Make an initial AJAX call to get pagination data
    $.ajax({
      url: '/laundry/orders/',
      type: 'GET',
      data: {
        'page': currentPage
      },
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      success: function (data) {
        console.log('Initial pagination data:', data);
        updatePagination(data);
        setupActionButtons();
        updateSelectAllState();
      },
      error: function (xhr, status, error) {
        console.error('Error initializing pagination:', error);
      }
    });
  }

  function updateSelectAllState() {
    const totalCheckboxes = $('.order-checkbox').length;
    const checkedCheckboxes = $('.order-checkbox:checked').length;
    const selectAllCheckbox = $('input[type="checkbox"]:first');
    const bulkDeleteBtn = $('#bulk-delete-btn');

    console.log(`Checkboxes: ${checkedCheckboxes}/${totalCheckboxes} checked`);

    if (checkedCheckboxes === 0) {
      selectAllCheckbox.prop('checked', false);
      selectAllCheckbox.prop('indeterminate', false);
      bulkDeleteBtn.hide();
    } else if (checkedCheckboxes === totalCheckboxes) {
      selectAllCheckbox.prop('checked', true);
      selectAllCheckbox.prop('indeterminate', false);
      bulkDeleteBtn.show();
    } else {
      selectAllCheckbox.prop('checked', false);
      selectAllCheckbox.prop('indeterminate', true);
      bulkDeleteBtn.show();
    }
  }

  function getSelectedOrderIds() {
    const selectedIds = [];
    $('.order-checkbox:checked').each(function () {
      selectedIds.push($(this).val());
    });
    console.log('Selected order IDs:', selectedIds);
    return selectedIds;
  }

  function getSelectedOrderCount() {
    return $('.order-checkbox:checked').length;
  }

  // Search functionality
  $('.search-bar').on('keyup', function () {
    let query = $(this).val();
    console.log('Search query:', query);

    $.ajax({
      url: '/laundry/orders/',
      type: 'GET',
      data: {
        'search': query
      },
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      success: function (data) {
        console.log('Search results:', data);
        $('#orders-container').html(data.html);
        updatePagination(data);
        setupActionButtons(); // Re-setup action buttons after content update
        updateSelectAllState(); // Reset select all state after content update
      },
      error: function (xhr, status, error) {
        console.error('AJAX Error:', error);
      }
    });
  });

  // Filter button functionality
  $('.btn-outline-secondary').first().on('click', function () {
    console.log('Filter button clicked');
    Swal.fire({
      title: 'Filter Orders',
      html: `
        <div class="mb-3">
          <label class="form-label">Status</label>
          <select class="form-select" id="filter-status">
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: 'Apply Filter',
      cancelButtonText: 'Cancel',
      preConfirm: () => {
        return document.getElementById('filter-status').value;
      }
    }).then((result) => {
      if (result.isConfirmed) {
        const status = result.value;
        console.log('Filtering by status:', status);
        $.ajax({
          url: '/laundry/orders/',
          type: 'GET',
          data: {
            'status': status
          },
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          },
          success: function (data) {
            console.log('Filter results:', data);
            $('#orders-container').html(data.html);
            updatePagination(data);
            setupActionButtons();
            updateSelectAllState(); // Reset select all state after content update
          },
          error: function (xhr, status, error) {
            console.error('AJAX Error:', error);
          }
        });
      }
    });
  });

  // Sort button functionality
  $('.btn-outline-secondary').eq(1).on('click', function () {
    console.log('Sort button clicked');
    Swal.fire({
      title: 'Sort Orders',
      html: `
        <div class="mb-3">
          <label class="form-label">Sort By</label>
          <select class="form-select" id="sort-by">
            <option value="-created_at">Newest First</option>
            <option value="created_at">Oldest First</option>
            <option value="guest__name">Guest Name A-Z</option>
            <option value="-guest__name">Guest Name Z-A</option>
            <option value="status">Status A-Z</option>
            <option value="-status">Status Z-A</option>
          </select>
        </div>
      `,
      showCancelButton: true,
      confirmButtonText: 'Apply Sort',
      cancelButtonText: 'Cancel',
      preConfirm: () => {
        return document.getElementById('sort-by').value;
      }
    }).then((result) => {
      if (result.isConfirmed) {
        const sort = result.value;
        console.log('Sorting by:', sort);
        $.ajax({
          url: '/laundry/orders/',
          type: 'GET',
          data: {
            'sort': sort
          },
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          },
          success: function (data) {
            console.log('Sort results:', data);
            $('#orders-container').html(data.html);
            updatePagination(data);
            setupActionButtons();
            updateSelectAllState(); // Reset select all state after content update
          },
          error: function (xhr, status, error) {
            console.error('AJAX Error:', error);
          }
        });
      }
    });
  });

  // Pagination click handler
  $(document).on('click', '.pagination .page-link', function (e) {
    e.preventDefault();
    const page = $(this).data('page');
    if (page) {
      console.log('Navigating to page:', page);
      loadPage(page);
    }
  });

  // Pages dropdown handler
  $(document).on('change', '#pages', function () {
    const page = $(this).val();
    if (page) {
      console.log('Pages dropdown changed to page:', page);
      loadPage(page);
    }
  });

  // Bulk delete button handler
  $(document).on('click', '#bulk-delete-btn', function () {
    console.log('Bulk delete button clicked');
    deleteSelectedOrders();
  });

  // Setup action buttons
  setupActionButtons();

  function loadPage(page) {
    const currentSearch = $('.search-bar').val();
    const currentStatus = $('.btn-outline-secondary').first().data('current-status') || '';
    const currentSort = $('.btn-outline-secondary').eq(1).data('current-sort') || '-created_at';

    const params = {
      'page': page
    };

    if (currentSearch) params.search = currentSearch;
    if (currentStatus) params.status = currentStatus;
    if (currentSort) params.sort = currentSort;

    $.ajax({
      url: '/laundry/orders/',
      type: 'GET',
      data: params,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      success: function (data) {
        console.log('Page load results:', data);
        $('#orders-container').html(data.html);
        updatePagination(data);
        setupActionButtons();
        updateSelectAllState(); // Reset select all state after content update
      },
      error: function (xhr, status, error) {
        console.error('AJAX Error:', error);
      }
    });
  }

  function updatePagination(data) {
    if (data.total_pages && data.total_pages > 1) {
      let paginationHTML = '';

      // Previous button
      if (data.has_previous) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${data.current_page - 1}">Previous</a></li>`;
      }

      // Page numbers
      const startPage = Math.max(1, data.current_page - 2);
      const endPage = Math.min(data.total_pages, data.current_page + 2);

      for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === data.current_page ? 'active' : '';
        paginationHTML += `<li class="page-item ${activeClass}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
      }

      // Next button
      if (data.has_next) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${data.current_page + 1}">Next</a></li>`;
      }

      $('.pagination').html(paginationHTML);

      // Update the pages dropdown
      const pagesSelect = $('#pages');
      if (pagesSelect.length) {
        pagesSelect.html('');
        for (let i = 1; i <= data.total_pages; i++) {
          const selected = i === data.current_page ? 'selected' : '';
          pagesSelect.append(`<option value="${i}" ${selected}>${i}/${data.total_pages}</option>`);
        }
      }
    }
  }

  function setupActionButtons() {
    console.log('Setting up action buttons...');

    // View button functionality
    $('.view-order-btn').off('click').on('click', function (e) {
      e.preventDefault();
      const orderId = $(this).data('order-id');
      console.log('View button clicked for order:', orderId);
      viewOrder(orderId);
    });

    // Edit button functionality
    $('.edit-order-btn').off('click').on('click', function (e) {
      e.preventDefault();
      const orderId = $(this).data('order-id');
      console.log('Edit button clicked for order:', orderId);
      editOrder(orderId);
    });

    // Delete button functionality
    $('.delete-order-btn').off('click').on('click', function (e) {
      e.preventDefault();
      const orderId = $(this).data('order-id');
      console.log('Delete button clicked for order:', orderId);
      deleteOrder(orderId);
    });
  }

  function viewOrder(orderId) {
    console.log('Viewing order:', orderId);
    $.ajax({
      url: `/laundry/orders/${orderId}/view/`,
      type: 'GET',
      success: function (data) {
        console.log('Order data:', data);
        Swal.fire({
          title: `Order #${data.id}`,
          html: `
            <div class="text-start">
              <p><strong>Guest:</strong> ${data.guest_name}</p>
              <p><strong>Room:</strong> ${data.room_number}</p>
              <p><strong>Service:</strong> ${data.service_type}</p>
              <p><strong>Bags:</strong> ${data.no_of_bags}</p>
              <p><strong>Specifications:</strong> ${data.specifications || 'None'}</p>
              <p><strong>Date:</strong> ${data.date_time}</p>
              <p><strong>Payment Method:</strong> ${data.payment_method === 'cash' ? 'Cash' : data.payment_method === 'room' ? 'Charge to Room' : data.payment_method}</p>
              <p><strong>Total:</strong> $${data.total_amount}</p>
              <p><strong>Status:</strong> ${data.status}</p>
              <p><strong>Created:</strong> ${data.created_at}</p>
            </div>
          `,
          confirmButtonText: 'Close'
        });
      },
      error: function (xhr, status, error) {
        console.error('Error viewing order:', error);
        Swal.fire('Error', 'Failed to load order details', 'error');
      }
    });
  }

  function editOrder(orderId) {
    console.log('Editing order:', orderId);
    $.ajax({
      url: `/laundry/orders/${orderId}/edit/`,
      type: 'GET',
      success: function (data) {
        console.log('Edit order data:', data);
        Swal.fire({
          title: `Edit Order #${data.id}`,
          html: `
            <form id="edit-order-form">
              <div class="mb-3">
                <label class="form-label">Service Type</label>
                <select class="form-select" id="edit-service-type">
                  <option value="Wash and Fold" ${data.service_type === 'Wash and Fold' ? 'selected' : ''}>Wash and Fold</option>
                  <option value="Dry Clean" ${data.service_type === 'Dry Clean' ? 'selected' : ''}>Dry Clean</option>
                  <option value="Press Only" ${data.service_type === 'Press Only' ? 'selected' : ''}>Press Only</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Number of Bags</label>
                <input type="number" class="form-control" id="edit-no-bags" value="${data.no_of_bags}" min="1">
              </div>
              <div class="mb-3">
                <label class="form-label">Specifications</label>
                <textarea class="form-control" id="edit-specifications">${data.specifications}</textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">Status</label>
                <select class="form-select" id="edit-status">
                  <option value="pending" ${data.status === 'pending' ? 'selected' : ''}>Pending</option>
                  <option value="in_progress" ${data.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                  <option value="completed" ${data.status === 'completed' ? 'selected' : ''}>Completed</option>
                  <option value="cancelled" ${data.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
              </div>
            </form>
          `,
          showCancelButton: true,
          confirmButtonText: 'Save Changes',
          cancelButtonText: 'Cancel',
          preConfirm: () => {
            return {
              service_type: document.getElementById('edit-service-type').value,
              no_of_bags: parseInt(document.getElementById('edit-no-bags').value),
              specifications: document.getElementById('edit-specifications').value,
              status: document.getElementById('edit-status').value
              // Payment method is disabled and not included in the update
            };
          }
        }).then((result) => {
          if (result.isConfirmed) {
            console.log('Saving order changes:', result.value);
            $.ajax({
              url: `/laundry/orders/${orderId}/edit/`,
              type: 'POST',
              data: JSON.stringify(result.value),
              contentType: 'application/json',
              headers: {
                'X-CSRFToken': getCookie('csrftoken')
              },
              success: function (response) {
                console.log('Save response:', response);
                if (response.success) {
                  Swal.fire('Success', response.message, 'success');
                  // Refresh the orders list
                  location.reload();
                } else {
                  Swal.fire('Error', response.message, 'error');
                }
              },
              error: function (xhr, status, error) {
                console.error('Error saving order:', error);
                Swal.fire('Error', 'Failed to update order', 'error');
              }
            });
          }
        });
      },
      error: function (xhr, status, error) {
        console.error('Error loading order for edit:', error);
        Swal.fire('Error', 'Failed to load order details', 'error');
      }
    });
  }

  function deleteOrder(orderId) {
    console.log('Deleting order:', orderId);
    Swal.fire({
      title: 'Delete Order',
      text: 'Are you sure you want to delete this order?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel'
    }).then((result) => {
      if (result.isConfirmed) {
        $.ajax({
          url: `/laundry/orders/${orderId}/delete/`,
          type: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken')
          },
          success: function (response) {
            console.log('Delete response:', response);
            if (response.success) {
              Swal.fire('Success', response.message, 'success');
              // Remove the order row from the table
              $(`[data-order-id="${orderId}"]`).remove();
            } else {
              Swal.fire('Error', response.message, 'error');
            }
          },
          error: function (xhr, status, error) {
            console.error('Error deleting order:', error);
            Swal.fire('Error', 'Failed to delete order', 'error');
          }
        });
      }
    });
  }

  function deleteSelectedOrders() {
    const selectedIds = getSelectedOrderIds();
    const selectedCount = selectedIds.length;

    if (selectedCount === 0) {
      Swal.fire('No Selection', 'Please select at least one order to delete.', 'info');
      return;
    }

    const message = selectedCount === 1
      ? 'Are you sure you want to delete this order?'
      : `Are you sure you want to delete ${selectedCount} selected orders?`;

    Swal.fire({
      title: 'Delete Orders',
      text: message,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel'
    }).then((result) => {
      if (result.isConfirmed) {
        // Delete each selected order
        let deletedCount = 0;
        let errorCount = 0;

        selectedIds.forEach((orderId, index) => {
          $.ajax({
            url: `/laundry/orders/${orderId}/delete/`,
            type: 'POST',
            headers: {
              'X-CSRFToken': getCookie('csrftoken')
            },
            success: function (response) {
              if (response.success) {
                deletedCount++;
                // Remove the order row from the table
                $(`[data-order-id="${orderId}"]`).remove();
              } else {
                errorCount++;
              }

              // Check if all deletions are complete
              if (deletedCount + errorCount === selectedCount) {
                if (errorCount === 0) {
                  Swal.fire('Success', `Successfully deleted ${deletedCount} order(s).`, 'success');
                } else {
                  Swal.fire('Partial Success', `Deleted ${deletedCount} order(s), ${errorCount} failed.`, 'warning');
                }
                // Reset select all checkbox
                updateSelectAllState();
              }
            },
            error: function (xhr, status, error) {
              errorCount++;
              console.error('Error deleting order:', error);

              // Check if all deletions are complete
              if (deletedCount + errorCount === selectedCount) {
                if (errorCount === selectedCount) {
                  Swal.fire('Error', 'Failed to delete any orders.', 'error');
                } else {
                  Swal.fire('Partial Success', `Deleted ${deletedCount} order(s), ${errorCount} failed.`, 'warning');
                }
                // Reset select all checkbox
                updateSelectAllState();
              }
            }
          });
        });
      }
    });
  }

  // Utility function to get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});