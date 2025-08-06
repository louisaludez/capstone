
  $(document).ready(function () {
    const deleteButtons = document.querySelectorAll(".delete-order-btn");
    deleteButtons.forEach((button) => {
        button.addEventListener("click", (e) => {
            const orderId = e.target.closest(".row").dataset.orderId;
            Swal.fire({
                title: "Are you sure?",
                text: "You won't be able to revert this!",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Yes, delete it!",
                cancelButtonText: "No, keep it"
            }).then((result) => {
                if (result.isConfirmed) {
                    // Call the delete API
                    fetch(`/laundry/orders/${orderId}/delete/`, {
                        method: "DELETE",
                        headers: {
                            "X-CSRFToken": getCookie("csrftoken")
                        }
                    }).then((response) => {
                        if (response.ok) {
                            Swal.fire("Deleted!", "Your file has been deleted.", "success");
                            // Remove the order from the DOM
                            e.target.closest(".row").remove();
                        } else {
                            Swal.fire("Error!", "There was an error deleting your file.", "error");
                        }
                    });
                }
            });
        });
    });




    $('.search-bar').on('keyup', function () {
      let query = $(this).val();

      $.ajax({
        url: '/laundry/orders/',
        type: 'GET',
        data: {
          'search': query
        },
        success: function (data) {
          $('#orders-container').html(data.html);
        },
        error: function (xhr, status, error) {
          console.error('AJAX Error:', error);
        }
      });
    });
  });