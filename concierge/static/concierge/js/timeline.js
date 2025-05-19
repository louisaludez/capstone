document.addEventListener("DOMContentLoaded", function () {
  // Handle checkbox interactions
  const checkboxes = document.querySelectorAll(".request-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const row = this.closest(".timeline-row");
      if (this.checked) {
        row.style.backgroundColor = "#f8f9fa";
      } else {
        row.style.backgroundColor = "";
      }
    });
  });

  // Handle view button clicks
  const viewButtons = document.querySelectorAll(".view-btn");
  viewButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const row = this.closest(".timeline-row");
      const requestId = row.dataset.requestId;
      window.location.href = `/concierge/request/${requestId}/`;
    });
  });

  // Handle edit button clicks
  const editButtons = document.querySelectorAll(".edit-btn");
  editButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const row = this.closest(".timeline-row");
      const requestId = row.dataset.requestId;
      window.location.href = `/concierge/request/${requestId}/edit/`;
    });
  });

  // Handle delete button clicks
  const deleteButtons = document.querySelectorAll(".delete-btn");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const row = this.closest(".timeline-row");
      const requestId = row.dataset.requestId;

      if (confirm("Are you sure you want to delete this request?")) {
        fetch(`/concierge/request/${requestId}/delete/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              row.remove();
            } else {
              alert("Error deleting request");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("Error deleting request");
          });
      }
    });
  });

  // Helper function to get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
