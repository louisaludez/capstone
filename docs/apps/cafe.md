### Cafe Module

Models: `CafeCategory`, `CafeItem`, `CafeOrder`, `CafeOrderItem`

#### GET `/cafe/staff/home/`
- Lists items, counts by category. Query params: `search`, `category`.

#### GET `/cafe/search-items-ajax/`
- Query: `search`, `category`
- Returns HTML snippet of item cards.

#### POST `/cafe/staff/create-order/` (csrf_exempt)
- JSON body:
  - items: [{ name, quantity, price }]
  - subtotal, total, cash_tendered?
  - guest: guest_id
  - dine_type: "Dine In" | "Takeout"
  - payment_method: "Cash Payment" | "Charge to room" | "Card Payment"
  - card: string (if card payment)
- Maps to model choices, creates `CafeOrder` + `CafeOrderItem` rows.
- If charged to room, increments `Guest.cafe_billing`.
- Response: `{ message, order_id }` or error.

#### GET `/cafe/staff/orders/`
- Renders order lists split by service_type.

Models summary:
- `CafeOrder(payment_method: cash|room|card, service_type: dine_in|take_out, totals, guest?)`
- `CafeOrderItem(order, item, quantity, price, subtotal)`
