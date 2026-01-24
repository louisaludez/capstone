from django.template.loader import render_to_string
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from chat.models import Message
from users.models import CustomUser
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
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
    guest = Guest.objects.filter(booking__status='Checked-in').distinct().order_by('name')
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
            print("\n=== STARTING CAFE ORDER CREATION ===")

            # Decode and parse JSON body
            raw_body = request.body.decode("utf-8")
            print("RAW BODY:", raw_body)
            data = json.loads(raw_body)
            print("PARSED DATA:", data)

            # Extract main order data
            items = data.get("items", [])
            subtotal = float(data.get("subtotal", 0))
            total = float(data.get("total", subtotal))
            cash_tendered = float(data.get("cash_tendered") or 0)
            change = float(data.get("change") or 0)
            guest_id = data.get("guest")
            dine_type = data.get("dine_type")
            payment_method = data.get("payment_method")
            card_number = str(data.get("card", "")).strip()

            print("--- ORDER INPUT DETAILS ---")
            print("Guest ID:", guest_id)
            print("Dine Type (Raw):", dine_type)
            print("Payment Method (Raw):", payment_method)
            print("Subtotal:", subtotal)
            print("Total:", total)
            print("Cash Tendered:", cash_tendered)
            print("Card Number:", card_number)
            print("Change:", change)
            # Map frontend text to model choices
            payment_map = { 
                "Cash Payment": "cash",
                "Charge to room": "room",
                "Card Payment": "card"
            }
            payment_method = payment_map.get(payment_method, payment_method)
            print("Mapped Payment Method:", payment_method)

            dine_map = {
                "Dine In": "dine_in",
                "Takeout": "take_out"
            }
            dine_type = dine_map.get(dine_type, dine_type)
            print("Mapped Dine Type:", dine_type)

            # Get guest instance
            guest = None
            if guest_id:
                guest = Guest.objects.get(id=int(guest_id))
                print("Fetched Guest:", guest.name)
            else:
                print("No guest provided (possible walk-in order).")

            # Prepare base order fields
            order_kwargs = {
                "customer_name": guest.name if guest else "Walk-in Customer",
                "guest": guest,
                "payment_method": payment_method,
                "service_type": dine_type,
                "subtotal": subtotal,
                "total": total
            }

            # Add card info if card payment
            if payment_method == "card":
                order_kwargs["card_number"] = card_number
                print("Added card info to order.")

            # Handle cash payment calculations
            if payment_method == "cash":
                order_kwargs["cash_tendered"] = cash_tendered
                try:
                    order_kwargs["change"] = max(0.0, cash_tendered - total)
                except Exception as calc_error:
                    print("Error computing change:", calc_error)
                    order_kwargs["change"] = 0.0
                print("Cash Payment - Tendered:", cash_tendered, "Change:", order_kwargs["change"])

            print("--- ORDER KWARGS PREPARED ---")
            for key, val in order_kwargs.items():
                print(f"{key}: {val}")

            # Create CafeOrder
            order = CafeOrder.objects.create(**order_kwargs)
            print("CafeOrder created with ID:", order.id)

            # Create order items
            print("--- CREATING ORDER ITEMS ---")
            for item_data in items:
                item_name = item_data.get("name")
                quantity = int(item_data.get("quantity", 0))
                price = float(item_data.get("price", 0))
                subtotal_item = price * quantity

                print(f"Processing Item: {item_name} | Qty: {quantity} | Price: {price} | Subtotal: {subtotal_item}")

                try:
                    cafe_item = CafeItem.objects.get(name=item_name)
                    CafeOrderItem.objects.create(
                        order=order,
                        item=cafe_item,
                        quantity=quantity,
                        price=price,
                        subtotal=subtotal_item
                    )
                    print(f"Added item '{item_name}' to order {order.id}")
                except CafeItem.DoesNotExist:
                    print(f"ERROR: Item '{item_name}' not found in database.")
                    return JsonResponse({"error": f"Item '{item_name}' not found"}, status=404)

            # Handle charge-to-room payment
            if payment_method == "room" and guest:
                print("Payment method: ROOM CHARGE. Updating guest billing.")
                print("Previous guest.cafe_billing:", guest.cafe_billing)
                new_billing = float(guest.cafe_billing or 0) + total
                guest.cafe_billing = str(new_billing)
                guest.save()
                print("Updated guest.cafe_billing to:", guest.cafe_billing)

            print("=== ORDER CREATION SUCCESSFUL ===")
            return JsonResponse({
                "message": "Order placed successfully",
                "order_id": order.id
            })

        except Exception as e:
            import traceback
            print("=== ERROR OCCURRED DURING ORDER CREATION ===")
            print("ERROR MESSAGE:", e)
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

    print("Invalid request method (not POST).")
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


def staff_cafe_orders(request):
    dine_in_orders = CafeOrder.objects.filter(service_type='dine_in').exclude(status='done').order_by('-order_date')
    take_out_orders = CafeOrder.objects.filter(service_type='take_out').exclude(status='done').order_by('-order_date')

    context = {
        'dine_in_orders': dine_in_orders,
        'take_out_orders': take_out_orders,
    }
    return render(request, 'cafe/staff/orders.html', context)


@csrf_exempt
def mark_order_done(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    order = get_object_or_404(CafeOrder, id=order_id)
    order.status = 'done'
    order.save(update_fields=['status'])
    return JsonResponse({'status': 'ok'})
def cafe_messenger(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')
    # Base on app service, not user role
    current_service = 'Cafe'

    # Build a deterministic room name based on simplified roles (order-insensitive)
    def simplify_role(role):
        mapping = {
            'staff_personnel': 'Personnel', 'manager_personnel': 'Personnel', 'personnel': 'Personnel', 'staff': 'Personnel', 'manager': 'Personnel',
            'staff_concierge': 'Concierge', 'manager_concierge': 'Concierge',
            'staff_laundry': 'Laundry', 'manager_laundry': 'Laundry',
            'staff_cafe': 'Cafe', 'manager_cafe': 'Cafe',
            'staff_room_service': 'Room Service', 'manager_room_service': 'Room Service',
            'admin': 'Admin', 'Admin': 'Admin'
        }
        return mapping.get(role, role)

    simplified = sorted([simplify_role(current_service), simplify_role(receiver_role)])
    room_name = f"chat_{'_'.join([s.replace(' ', '_') for s in simplified])}"

    # ULTRA-SIMPLE: ONLY filter by conversation_room - nothing else!
    # This ensures each chatbox ONLY shows messages for that specific conversation
    try:
        # Check if conversation_room field exists
        Message._meta.get_field('conversation_room')
        field_exists = True
    except:
        field_exists = False
    
    if field_exists:
        # ONLY show messages with the exact conversation_room - no fallback, no exceptions!
        messages_qs = Message.objects.filter(conversation_room=room_name).order_by('created_at')
    else:
        # If field doesn't exist (migration not run), compute room on-the-fly for each message
        all_messages = Message.objects.all()
        matching_messages = []
        
        for msg in all_messages:
            # Compute room for this message the same way it's computed when saving
            sender_context = simplify_role(msg.sender_service) if msg.sender_service else simplify_role(msg.sender_role)
            receiver_context = simplify_role(msg.receiver_role)
            conv_roles = sorted([sender_context, receiver_context])
            msg_room = f"chat_{'_'.join([r.replace(' ', '_') for r in conv_roles])}"
            
            if msg_room == room_name:
                matching_messages.append(msg.id)
        
        messages_qs = Message.objects.filter(id__in=matching_messages).order_by('created_at')
    
    # Debug logging
    print(f"\n[CAFE MESSENGER] ========================================")
    print(f"[CAFE MESSENGER] Viewing chat with: {receiver_role}")
    print(f"[CAFE MESSENGER] Current service: {current_service}")
    print(f"[CAFE MESSENGER] Conversation room: {room_name}")
    print(f"[CAFE MESSENGER] Field exists: {field_exists}")
    print(f"[CAFE MESSENGER] Found {messages_qs.count()} messages in this room")
    
    # Show sample messages
    for msg in messages_qs[:5]:
        print(f"  - ID={msg.id}, conversation_room='{getattr(msg, 'conversation_room', 'N/A')}', sender_service='{msg.sender_service}', sender_role='{msg.sender_role}', receiver_role='{msg.receiver_role}'")
    print(f"[CAFE MESSENGER] ========================================\n")

    # Attach sender usernames for display consistency
    for msg in messages_qs:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"

    return render(request, 'cafe/staff/messenger.html', {
        'room_name': room_name,
        'receiver_role': receiver_role,
        'messages': messages_qs,
        'current_user_id': request.user.id,
        'current_service': current_service,
    })