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
      // Add view functionality here
    });
  });

  // Handle edit button clicks
  const editButtons = document.querySelectorAll(".edit-btn");
  editButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const row = this.closest(".timeline-row");
      // Add edit functionality here
    });
  });

  // Handle delete button clicks
  const deleteButtons = document.querySelectorAll(".delete-btn");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const row = this.closest(".timeline-row");
      if (confirm("Are you sure you want to delete this request?")) {
        // Add delete functionality here
      }
    });
  });
});
