from django.template.loader import render_to_string
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cafe.models import *
from staff.models import Guest

def search_items_ajax(request):
    search_term = request.GET.get('search', '')
    category = request.GET.get('category', '')
 
    items = CafeItem.objects.all()

    if search_term:
        items = items.filter(name__icontains=search_term)
    
    if category:
        items = items.filter(category__name__icontains=category)

    html = render_to_string('cafe/staff/includes/item_cards.html', {'items': items})
    return JsonResponse({'html': html})
def staff_cafe_home(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    guest = Guest.objects.all()
    items = CafeItem.objects.all().order_by('category','name')
    total_items = items.count()
    pasta_count = items.filter(category="1").count()
    pastry_count = items.filter(category="2").count()
    hot_drinks_count = items.filter(category="3").count()
    cold_drinks_count = items.filter(category="4").count()
    sandwiches_count = items.filter(category="5").count()

    if search_query:
        items = items.filter(name__icontains=search_query)

    if category_filter:
        items = items.filter(category__name__iexact=category_filter)

    context = {
        'items': items,
        'categories': CafeCategory.objects.all(),
        'search_query': search_query,
        'category_filter': category_filter,
        'guests': guest,
         'total_items': total_items,
        'pasta_count': pasta_count,
        'pastry_count': pastry_count,
        'hot_drinks_count': hot_drinks_count,
        'cold_drinks_count': cold_drinks_count,
        'sandwiches_count': sandwiches_count,
    }
    return render(request, 'cafe/staff/home.html', context)



@csrf_exempt
def create_order(request):
    if request.method == "POST":
        try:
            raw_body = request.body.decode("utf-8")
            print("RAW BODY:", raw_body)

            data = json.loads(raw_body)
            print("PARSED DATA:", data)

            items = data.get("items", [])
            subtotal = float(data.get("subtotal", 0))
            total = float(data.get("total", subtotal))
            cash_tendered = float(data.get("cash_tendered") or 0)
            guest_id = data.get("guest")
            dine_type = data.get("dine_type")
            payment_method = data.get("payment_method")
            customer_name = data.get("customer_name", "")
            card_number = str(data.get("card", "")).strip()

            # Map payment and service type from frontend text to model choices
            payment_map = { 
                "Cash Payment": "cash",
                "Charge to room": "room",
                "Card Payment": "card"
            }
            payment_method = payment_map.get(payment_method, payment_method)

            dine_map = {
                "Dine In": "dine_in",
                "Takeout": "take_out"
            }
            dine_type = dine_map.get(dine_type, dine_type)

            # Get guest instance if provided
            guest = Guest.objects.get(id=int(guest_id)) if guest_id else None

            # Prepare order kwargs
            order_kwargs = {
                "customer_name": customer_name,
                "guest": guest,
                "payment_method": payment_method,
                "service_type": dine_type,
                "subtotal": subtotal,
                "total": total
            }

            # Add card number only if payment method is card
            if payment_method == "card":
                order_kwargs["card_number"] = card_number

            # Create the CafeOrder
            order = CafeOrder.objects.create(**order_kwargs)

            # Add items to CafeOrderItem
            for item_data in items:
                item_name = item_data.get("name")
                quantity = int(item_data.get("quantity"))
                price = float(item_data.get("price"))
                subtotal_item = price * quantity

                try:
                    cafe_item = CafeItem.objects.get(name=item_name)
                except CafeItem.DoesNotExist:
                    return JsonResponse({"error": f"Item '{item_name}' not found"}, status=404)

                CafeOrderItem.objects.create(
                    order=order,
                    item=cafe_item,
                    quantity=quantity,
                    price=price,
                    subtotal=subtotal_item
                )

            # If payment is charged to room, update guest billing
            if payment_method == "room" and guest:
                guest.cafe_billing = str(float(guest.cafe_billing) + total)
                guest.save()

            return JsonResponse({
                "message": "Order placed successfully",
                "order_id": order.id
            })

        except Exception as e:
            import traceback
            print("ERROR:", e)
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


# def create_order(reques:t):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)

#             # Create main order
#             order = CafeOrder.objects.create(
#                 customer_name=data.get('customer_name', ''),
#                 payment_method=data['payment_method'],
#                 service_type=data['service_type'],
#                 subtotal=data['subtotal'],
#                 total=data['total']
#             )

#             # Add items
#             for item_data in data['items']:
#                 menu_item = CafeItem.objects.get(id=item_data['id'])
#                 CafeOrderItem.objects.create(
#                     order=order,
#                     item=menu_item,
#                     quantity=item_data['quantity'],
#                     price=menu_item.price,
#                     subtotal=item_data['quantity'] * menu_item.price
#                 )

#             return JsonResponse({'status': 'success', 'order_id': order.id})
        
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

#     return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)
