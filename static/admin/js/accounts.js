
  $(function () {
    
    // Initialize DataTable without its built-in search box
    var table = $("#usersTable").DataTable({
      paging: true,
      pageLength: 6,
      lengthChange: false,
      info: true,
      searching: false, // disable default search
      order: [], // disable initial sort
      columnDefs: [{ orderable: false, targets: [0, 5] }],
    });

    // Custom search input and button hooked to DataTables search
    $("#customSearch").on("input", function () {
      table.search(this.value).draw();
    });
    $("#customSearchBtn").on("click", function () {
      table.search($("#customSearch").val()).draw();
    });

    // Initialize toast
    const toast = new bootstrap.Toast(
      document.getElementById("notificationToast"),
      {
        animation: true,
        autohide: true,
        delay: 3000,
      }
    );

    // Function to show notification
    function showNotification(title, message, isSuccess = true) {
      const toastEl = document.getElementById("notificationToast");
      const toastTitle = document.getElementById("toastTitle");
      const toastMessage = document.getElementById("toastMessage");
      let countdown = 3; // 3 seconds countdown

      // Update toast content
      toastTitle.textContent = title;
      toastMessage.textContent = `${message} (${countdown}s)`;

      // Update toast style based on success/error
      if (isSuccess) {
        toastEl.classList.remove("bg-danger", "text-white");
        toastEl.classList.add("bg-success", "text-white");
      } else {
        toastEl.classList.remove("bg-success", "text-white");
        toastEl.classList.add("bg-danger", "text-white");
      }

      // Show toast
      toast.show();

      // Start countdown
      const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          toastMessage.textContent = `${message} (${countdown}s)`;
        } else {
          clearInterval(countdownInterval);
          toast.hide();
        }
      }, 1000);
    }

    // Function to update table row
    function updateTableRow(userId, data) {
      const row = table.row($(`tr[data-user-id="${userId}"]`));
      if (row.length) {
        // Format the date to Manila timezone
        const dateJoined = new Date(data.date_joined);
        const manilaOptions = {
          timeZone: "Asia/Manila",
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        };
        const formattedDate = dateJoined.toLocaleString("en-US", manilaOptions);

        const newData = [
          `<input type="checkbox" />`,
          data.id,
          data.username,
          data.role,
          formattedDate,
          `<button class="btn btn-sm btn-link p-0 me-2 view-user" data-user-id="${data.id}">
            <i class="bi bi-eye"></i>
          </button>
          <button class="btn btn-sm btn-link p-0 me-2 edit-user" data-user-id="${data.id}">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-link p-0 text-danger delete-user" data-user-id="${data.id}">
            <i class="bi bi-trash"></i>
          </button>`,
        ];
        row.data(newData).draw(false);
      }
    }

    // Function to add new row to table
    function addTableRow(data) {
      // Format the date to Manila timezone
      const dateJoined = new Date(data.date_joined);
      const manilaOptions = {
        timeZone: "Asia/Manila",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      };
      const formattedDate = dateJoined.toLocaleString("en-US", manilaOptions);

      const newRow = [
        `<input type="checkbox" />`,
        data.id,
        data.username,
        data.role,
        formattedDate,
        `<button class="btn btn-sm btn-link p-0 me-2 view-user" data-user-id="${data.id}">
          <i class="bi bi-eye"></i>
        </button>
        <button class="btn btn-sm btn-link p-0 me-2 edit-user" data-user-id="${data.id}">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-link p-0 text-danger delete-user" data-user-id="${data.id}">
          <i class="bi bi-trash"></i>
        </button>`,
      ];
      table.row.add(newRow).draw(false);
    }

    // Function to remove row from table
    function removeTableRow(userId) {
      const row = table.row($(`tr[data-user-id="${userId}"]`));
      if (row.length) {
        row.remove().draw(false);
      }
    }

    // View User - Using event delegation
   $(document).on("click", ".view-user", function () {
  const userId = $(this).data("user-id");

  $.get(`/adminNew/accounts/view-user/${userId}/`, function (data) {
    $("#viewUsername").text(data.username);
    $("#viewEmail").text(data.email);
    $("#viewRole").text(data.role);

    const manilaOptions = {
      timeZone: "Asia/Manila",
      year: "numeric",
      month: "long",    // F = full month
      day: "numeric",   // j = day without leading zero
      hour: "numeric",  // g = hour without leading zero
      minute: "2-digit",// i = zero-padded minute
      hour12: true      // A = AM/PM
    };

    // Format date joined
    const dateJoined = new Date(data.date_joined);
    $("#viewDateJoined").text(dateJoined.toLocaleString("en-US", manilaOptions));

    // Format last login
    let lastLoginText = "Never";
    if (
      data.last_login &&
      data.last_login !== "None" &&
      data.last_login !== "null"
    ) {
      const lastLogin = new Date(data.last_login);
      if (!isNaN(lastLogin.getTime())) {
        lastLoginText = lastLogin.toLocaleString("en-US", manilaOptions);
      }
    }
    $("#viewLastLogin").text(lastLoginText);

    // Show the modal
    $("#viewUserModal").modal("show");
  });
});

    // Edit User - Using event delegation
    $(document).on("click", ".edit-user", function () {
      const userId = $(this).data("user-id");
      $.get(`/adminNew/accounts/edit-user/${userId}/`, function (data) {
        $("#editUserId").val(data.id);
        $("#editUsername").val(data.username);
        $("#editEmail").val(data.email);
        $("#editRole").val(data.role);
        $("#editPassword").val(""); // Clear password field
        $("#editUserModal").modal("show");
      });
    });

    // Handle Edit Form Submit
    $("#editUserForm").on("submit", function (e) {
      e.preventDefault();
      const userId = $("#editUserId").val();

      // Check if passwords match when a new password is provided
      const password = $("#editPassword").val();
      const confirmPassword = $("#editConfirmPassword").val();

      if (password && password !== confirmPassword) {
        showNotification("Error", "Passwords do not match.", false);
        return;
      }

      $.ajax({
        url: `/adminNew/accounts/edit-user/${userId}/`,
        type: "POST",
        data: $(this).serialize(),
        headers: {
          "X-CSRFToken": $('input[name="csrfmiddlewaretoken"]').val(),
        },
        success: function (response) {
          if (response.status === "success") {
            showNotification("Success", response.message, true);
            $("#editUserModal").modal("hide");
            // Refresh the page after a short delay
            setTimeout(() => {
              location.reload();
            }, 1500);
          } else {
            showNotification("Error", response.message, false);
          }
        },
        error: function () {
          showNotification(
            "Error",
            "An error occurred while updating the user.",
            false
          );
        },
      });
    });

    // Delete User - Using event delegation
    $(document).on("click", ".delete-user", function () {
      const userId = $(this).data("user-id");
      const userRole = $(this).closest("tr").find("td:eq(3)").text(); // Get user role from table
     
      // Check if this is an admin user
      if (userRole === "admin") {
        // Count total admin users
        let adminCount = 0;
        table.rows().every(function () {
          const role = this.data()[3]; // Role is in the 4th column
          if (role === "admin") {
            adminCount++;
          }
        });

        // If this is the last admin, prevent deletion
        if (adminCount <= 1) {
          showNotification(
            "Error",
            "Cannot delete the last admin user. At least one admin must remain in the system.",
            false
          );
          return;
        }
      }

      $("#deleteUserId").val(userId);
      $("#deleteUserModal").modal("show");
    });

    // Handle Delete Confirmation
    $("#confirmDelete").on("click", function () {
      const userId = $("#deleteUserId").val();
       const csrfToken = document.getElementById("csrf_token").value;
      $.ajax({
        url: `/adminNew/accounts/delete-user/${userId}/`,
        type: "POST",
        data: {
          csrfmiddlewaretoken: csrfToken,
        },
        success: function (response) {
          if (response.status === "success") {
            showNotification("Success", response.message, true);
            $("#deleteUserModal").modal("hide");
            // Refresh the page after a short delay
            setTimeout(() => {
              location.reload();
            }, 1500);
          } else {
            showNotification("Error", response.message, false);
          }
        },
        error: function () {
          showNotification(
            "Error",
            "An error occurred while deleting the user.",
            false
          );
        },
      });
    });

    // Handle Add User Form Submit
    $("#addUserForm").on("submit", function (e) {
      e.preventDefault();

      // Check if passwords match
      const password = $("#password").val();
      const confirmPassword = $("#confirmPassword").val();

      if (password !== confirmPassword) {
        showNotification("Error", "Passwords do not match.", false);
        return;
      }

      $.ajax({
        url: $(this).attr("action"),
        type: "POST",
        data: $(this).serialize(),
        success: function (response) {
          if (response.status === "success") {
            showNotification("Success", response.message, true);
            $("#addUserModal").modal("hide");
            $("#addUserForm")[0].reset();
            // Refresh the page after a short delay
            setTimeout(() => {
              location.reload();
            }, 1500);
          } else {
            showNotification("Error", response.message, false);
          }
        },
        error: function (xhr, errmsg, err) {
          showNotification(
            "Error",
            "An error occurred while adding the user. Please try again.",
            false
          );
        },
      });
    });
  });
