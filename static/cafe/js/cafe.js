document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector(".search-bar");
  const filterDivs = document.querySelectorAll(".filter-box");
  const rowItems = document.querySelector(".items");
  const subtotal = document.getElementById("subtotal");

  const totalText = document.getElementById("total");
  const dtButtons = document.querySelectorAll(".dt-button");
  const placeOrderBtn = document.querySelector(".po-btn");
  let currentCategory = "";
  let currentSearch = "";
  let currentSubtotalValue = 0;
  const detailsRow = document.querySelector(".row.details");
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

  const paymentDetailsTemplates = {
    "Cash Payment": `
    <div class="col-12 d-flex justify-content-between mb-2">
      <span>Subtotal</span>
      <input type="text" placeholder="0.00" disabled class="subtotal" id="subtotal" />
    </div>
    <div class="col-12 d-flex justify-content-between mb-2">
      <span>Cash Tendered</span>
      <input type="text" id="cash-tentered" />
    </div>
    <div class="col-12 d-flex justify-content-between mb-2">
      <span>Change</span>
      <input type="text" value="0.00" disabled id="change" />
    </div>
    <div class="col-12 d-flex justify-content-between mb-2 total">
      <span>TOTAL</span>
      <span id="total">0.00</span>
    </div>
  `,
    "Card Payment": `
    <div class="col-12 d-flex justify-content-between mb-2">
      <span>Subtotal</span>
      <input type="text" placeholder="0.00" disabled class="subtotal" id="subtotal" />
    </div>
    <div class="col-12 d-flex justify-content-between mb-2">
      <span>Card Number</span>
      <input type="text" id="card-number" />
    </div>
    <div class="col-12 d-flex justify-content-between mb-2 total">
      <span>TOTAL</span>
      <span id="total">0.00</span>
    </div>
  `,
    "Charge to room": `
    <div class="col-12 d-flex justify-content-between mb-2 total">
      <span>TOTAL</span>
      <span id="total">0.00</span>
    </div>
  `
  };
  function bindCashTendered() {
    const cashTentered = document.getElementById("cash-tentered");
    if (!cashTentered) return;
    cashTentered.addEventListener("input", function () {
      console.log('sfsdf');
      const subtotalField = document.getElementById("subtotal");
      const stotal = parseFloat(subtotalField ? subtotalField.value : currentSubtotalValue) || 0;
      const tendered = parseFloat(this.value) || 0;
      let total = tendered - stotal;
      if (total < 0) total = 0;
      const change = document.getElementById("change");
      if (change) change.value = total.toFixed(2);

      const totalTextEl = document.getElementById("total");
      if (totalTextEl) totalTextEl.innerText = "P" + stotal.toFixed(2);
    });
  }
  function updateSubtotal(amount) {
    const subtotalField = document.getElementById("subtotal");

    let current = parseFloat(subtotalField ? subtotalField.value : currentSubtotalValue) || 0;

    let newTotal = current + amount;
    if (newTotal < 0) newTotal = 0;
    currentSubtotalValue = newTotal;

    // Update subtotal if it exists
    if (subtotalField) subtotalField.value = newTotal.toFixed(2);


    const totalTextEl = document.getElementById("total");
    if (totalTextEl) totalTextEl.innerText = "P" + newTotal.toFixed(2);
    bindCashTendered();

  }

  const paymentButtons = document.querySelectorAll(".pm");
  paymentButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      paymentButtons.forEach((b) => b.classList.remove("active"));
      this.classList.add("active");
      checkSelections();
      const method = this.textContent.trim();
      if (paymentDetailsTemplates[method]) {
        detailsRow.innerHTML = paymentDetailsTemplates[method];
        const subtotalField = document.getElementById("subtotal");
        if (subtotalField) subtotalField.value = currentSubtotalValue.toFixed(2);
        const totalTextEl = document.getElementById("total");
        if (totalTextEl) totalTextEl.innerText = "P" + currentSubtotalValue.toFixed(2);
        bindCashTendered();
      }
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
      "beforeend", `<div class="col-6 mb-2">
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
      const input = document.querySelector(`input[data-quantity= "${name}"]`);
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

  // Initial bind
  bindMenuCardEvents();

  placeOrderBtn.addEventListener("click", function () {
    const guest = document.getElementById("customer-select");
    let dineMethod = document.querySelector(".dt-button.active")?.textContent || "";
    let paymentMethod = document.querySelector(".pm.active")?.textContent || "";
    const cardnumber = document.getElementById("card-number")?.value || 0;
    const cashTentered = document.getElementById("cash-tentered")?.value || 0;

    const change = document.getElementById("change")?.value || 0;
    console.log("cash tendered", cashTentered);
    console.log("change", change);
    // Place order logic here
    const orderItems = [];
    document.querySelectorAll('input[data-quantity]').forEach(input => {
      orderItems.push({
        name: input.dataset.quantity,
        quantity: parseInt(input.value),
        price: parseFloat(input.dataset.price)
      });
    });
    $.ajax({
      url: "/cafe/staff/create-order/",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        items: orderItems,
        subtotal: subtotal.value,
        cash_tendered: cashTentered,
        change: change,
        guest: guest.value,
        dine_type: dineMethod,
        payment_method: paymentMethod,

        card: cardnumber,

      }),
      success: function (response) {
        Swal.fire({
          icon: "success",
          title: "Order placed successfully",
          showConfirmButton: false,
          timer: 1500
        }).then(() => {
          window.location.reload();
        });
      },
      error: function (error) {

        console.error("Error placing order:", error);
      }
    });
  });
});