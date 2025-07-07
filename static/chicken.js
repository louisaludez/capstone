document
  .getElementById("checkin-rooms")
  .addEventListener("click", function (event) {
    clearInterval(checkinTimerInterval);
    checkinTimerInterval = null;
    checkinModal.style.display = "none";
  });
