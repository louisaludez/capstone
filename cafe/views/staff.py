from django.shortcuts import render
from cafe.models import Items

from django.http import JsonResponse
from django.template.loader import render_to_string
def staff_cafe_home(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    items = Items.objects.all()

    if search_query:
        items = items.filter(item_name__icontains=search_query)

    if category_filter:
        items = items.filter(item_category__iexact=category_filter)

    context = {
        'items': items,
        'total_items': Items.objects.count(),
        'pasta_count': Items.objects.filter(item_category='Pasta').count(),
        'pastry_count': Items.objects.filter(item_category='Pastry').count(),
        'hot_drinks_count': Items.objects.filter(item_category__icontains='Hot Drinks').count(),
        'cold_drinks_count': Items.objects.filter(item_category__icontains='Cold Drinks').count(),
        'sandwiches_count': Items.objects.filter(item_category__icontains='Sandwiches').count(),
        'search_query': search_query,
        'category_filter': category_filter,
    }

    return render(request, 'cafe/staff/home.html', context)
def search_items_ajax(request):
    search_term = request.GET.get('search', '')
    category = request.GET.get('category', '')

    items = Items.objects.all()

    if search_term:
        items = items.filter(item_name__icontains=search_term)
    
    if category:
        items = items.filter(item_category__icontains=category)

    html = render_to_string('cafe/staff/includes/item_cards.html', {'items': items})
    print(html)
    return JsonResponse({'html': html})
