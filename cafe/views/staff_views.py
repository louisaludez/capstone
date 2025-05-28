from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..models import MenuItem, Order, OrderItem, OrderStatusHistory
from staff.models import Room
from decimal import Decimal
from chat.models import Message
from django.db import models
import json

def staff_cafe_home(request):
    return render(request,'staff_cafe/home.html')

def staff_cafe_orders(request):
    return render(request,'staff_cafe/orders.html')

@require_POST
def place_order(request):
    try:
        # Get order data from request
        data = json.loads(request.body)
        print("Received data:", data)  # Debug print

        items = data.get('items', [])
        quantities = data.get('quantities', [])
        customer_name = data.get('customer_name')
        room_number = data.get('room_number')
        order_type = data.get('order_type')
        payment_method = data.get('payment_method')
        cash_tendered = data.get('cash_tendered')
        special_instructions = data.get('special_instructions')

        print(f"Processing order: {customer_name}, {order_type}, {payment_method}")  # Debug print

        # Validate required fields
        if not items or not customer_name:
            return JsonResponse({
                'success': False,
                'error': 'Please add items and enter customer name'
            })

        # Handle room service orders
        room = None
        if order_type == 'room' and room_number:
            try:
                room = Room.objects.get(room_number=room_number)
            except Room.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Room {room_number} does not exist'
                })

        # Create the order
        order = Order.objects.create(
            room=room,
            cashier=request.user,
            status='pending',
            payment_method=payment_method,
            order_type=order_type,
            special_instructions=special_instructions
        )

        print(f"Created order: {order.order_number}")  # Debug print

        # Add cash tendered if payment method is cash
        if payment_method == 'cash' and cash_tendered:
            order.cash_tendered = Decimal(cash_tendered)
            order.save()

        # Create order items
        total_amount = Decimal('0.00')
        for item_id, quantity in zip(items, quantities):
            try:
                menu_item = MenuItem.objects.get(id=item_id)
                quantity = int(quantity)
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    price_at_time=menu_item.price
                )
                
                total_amount += menu_item.price * quantity
                print(f"Added item: {menu_item.name} x {quantity}")  # Debug print
                
            except MenuItem.DoesNotExist:
                order.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Menu item {item_id} does not exist'
                })
            except ValueError:
                order.delete()
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid quantity for item {item_id}'
                })

        # Update order total
        order.total_amount = total_amount
        order.save()

        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Order placed',
            created_by=request.user
        )

        print(f"Order completed: {order.order_number}")  # Debug print

        return JsonResponse({
            'success': True,
            'order_number': order.order_number
        })

    except Exception as e:
        print(f"Error placing order: {str(e)}")  # Debug print
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def staff_cafe_messages(request):
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "staff_cafe/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })