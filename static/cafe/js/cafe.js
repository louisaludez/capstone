document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector(".search-bar");
  const filterDivs = document.querySelectorAll(".filter-box");
  const rowItems = document.querySelector(".items");
  const subtotal = document.getElementById("subtotal");
  const cashTentered = document.getElementById("cash-tentered");
  const change = document.getElementById("change");
  const totalText = document.getElementById("total");
  const dtButtons = document.querySelectorAll(".dt-button");
  const placeOrderBtn = document.querySelector(".po-btn");
  let currentCategory = "";
  let currentSearch = "";
  const selectedNames = [];
  function checkSelections() {
    const dineSelected = document.querySelector(".dt-button.active");
    const paymentSelected = document.querySelector(".pm.active");

    if (dineSelected && paymentSelected) {
      placeOrderBtn.disabled = false;
    } else {
      placeOrderBtn.disabled = true;
    }
  }
  dtButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      dtButtons.forEach((b) => b.classList.remove("active"));
      this.classList.add("active");
      checkSelections();
    });
  });
  const paymentButtons = document.querySelectorAll(".pm");
  paymentButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      paymentButtons.forEach((b) => b.classList.remove("active"));
      this.classList.add("active");
      checkSelections();
    });
  });
  function fetchItems() {
    const url = `/cafe/search-items-ajax/?search=${currentSearch}&category=${currentCategory}`;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        document.getElementById("item-results").innerHTML = data.html;
        bindMenuCardEvents(); // Rebind click events
      });
  }

  searchInput.addEventListener("input", function () {
    currentSearch = this.value;
    fetchItems();
  });

  filterDivs.forEach((div) => {
    div.addEventListener("click", function () {
      currentCategory = this.dataset.category;
      fetchItems();
    });
  });

  function bindMenuCardEvents() {
    const menuCards = document.querySelectorAll(".menu-card");
    menuCards.forEach((div) => {
      div.addEventListener("click", function () {
        const name = this.dataset.name;
        const category = this.dataset.category;
        const price = this.dataset.price;
        addItem(name, category, price);
      });
    });
  }

  function addItem(name, category, price) {
    const priceValue = parseFloat(price) || 0;
    const input = document.querySelector(`input[data-quantity="${name}"]`);

    if (input) {
      const newQty = parseInt(input.value) + 1;
      input.value = newQty;
      updateSubtotal(priceValue);
      return;
    }

    // Add new item markup
    rowItems.insertAdjacentHTML(
      "beforeend",
      `
      <div class="col-6 mb-2">
        <div class="border rounded px-2 py-1" style="font-size: 0.85rem;">
          <strong style="font-size: 0.5rem;">${name}</strong><br />
          <small class="text-muted" style="font-size: 0.5rem;">${category}</small>
        </div>
      </div>
      <div class="col-6 d-flex align-items-center justify-content-between mb-2" style="font-size: 0.5rem;">
        <div>
          <div class="mb-1 text-end" style="font-size: 0.5rem;">${price}</div>
          <div class="input-group input-group-sm" style="font-size: 0.5rem;">
            <button class="btn btn-outline-dark btn-sm px-2 py-0 subtract-btn" data-quantity="${name}">−</button>
            <input type="text" class="form-control text-center py-0" value="1"
                   style="max-width: 30px; font-size: 0.85rem;" 
                   readonly data-quantity="${name}" data-price="${price}" />
            <button class="btn btn-outline-dark btn-sm px-2 py-0 add-btn" data-quantity="${name}">+</button>
          </div>
        </div>
      </div>
    `
    );

    selectedNames.push(name);
    updateSubtotal(priceValue);
  }

  function updateSubtotal(amount) {
    let current = parseFloat(subtotal.value) || 0;
    let newTotal = current + amount;
    if (newTotal < 0) newTotal = 0;
    subtotal.value = newTotal.toFixed(2);
    totalText.innerText = "P" + newTotal.toFixed(2);
  }

  function verify(myArray, myString) {
    return myArray
      .map((i) => i.trim().toLowerCase())
      .includes(myString.trim().toLowerCase());
  }

  // Delegated listener for + / - buttons
  if (rowItems) {
    rowItems.addEventListener("click", function (e) {
      const isAdd = e.target.classList.contains("add-btn");
      const isSubtract = e.target.classList.contains("subtract-btn");
      if (!isAdd && !isSubtract) return;

      const name = e.target.dataset.quantity;
      const input = document.querySelector(`input[data-quantity="${name}"]`);
      if (!input) return;

      const price = parseFloat(input.dataset.price);
      let quantity = parseInt(input.value);
      const oldQuantity = quantity;

      if (isAdd) {
        quantity++;
      } else if (isSubtract) {
        quantity--;
      }

      if (quantity <= 0) {
        // Remove both name & quantity column
        const nameCol = input.closest(".col-6.mb-2")?.previousElementSibling;
        const qtyCol = nameCol?.nextElementSibling;
        nameCol?.remove();
        qtyCol?.remove();
        updateSubtotal(-oldQuantity * price);
        const index = selectedNames.indexOf(name);
        if (index > -1) selectedNames.splice(index, 1);
      } else {
        input.value = quantity;
        const diff = quantity - oldQuantity;
        updateSubtotal(diff * price);
      }
    });
  }

  cashTentered.addEventListener("input", function () {
    const stotal = parseFloat(subtotal.value) || 0;
    const tendered = parseFloat(cashTentered.value) || 0;
    let total = tendered - stotal;
    if (total < 0) total = 0;
    change.value = total.toFixed(2);
    totalText.innerText = "P" + stotal.toFixed(2);
  });

  // Initial bind
  bindMenuCardEvents();
});
