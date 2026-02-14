import csv
from datetime import date

from django.apps import apps
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import get_resolver
from django.urls.resolvers import URLPattern
from django.utils import timezone

SCALE_EVENT_DATE = date(2026, 3, 5)

def get_stats_for_orders(orders, postfix=None, with_revenue=True):
    numbers_key = 'numbers'
    revenue_key = 'revenue'
    if postfix:
        numbers_key += postfix
        revenue_key += postfix

    results = {}
    results[numbers_key] = orders.count()
    if with_revenue:
        results[revenue_key] = sum(order.amount for order in orders)
    return results


def get_orders_data():
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_30 = today - timezone.timedelta(days=30)
    days_7 = today - timezone.timedelta(days=7)

    order_model = apps.get_model('reg23', 'Order')
    orders = order_model.objects.filter(valid=True)

    orders_data = {}
    orders_data['by_type'] = []
    orders_data |= get_stats_for_orders(orders)
    orders_data |= get_stats_for_orders(orders.filter(date__gt=days_30),
                                        postfix='_30')
    orders_data |= get_stats_for_orders(orders.filter(date__gt=days_7),
                                        postfix='_7')

    for payment_choice in order_model.payment_type.field.choices:
        orders_of_type = orders.filter(payment_type=payment_choice[0])

        data_payment_type = {}
        data_payment_type['name'] = payment_choice[1]
        data_payment_type |= get_stats_for_orders(orders_of_type)
        data_payment_type |= get_stats_for_orders(
            orders_of_type.filter(date__gt=days_30),
            postfix='_30',
            with_revenue=False)
        data_payment_type |= get_stats_for_orders(
            orders_of_type.filter(date__gt=days_7),
            postfix='_7',
            with_revenue=False)

        orders_data['by_type'].append(data_payment_type)

    return orders_data


@staff_member_required
def sales_dashboard(request, report_name):
    return render(request, 'reports_sales_dashboard.html', {
        'title': report_name,
        'orders': get_orders_data(),
    })


@staff_member_required
def index(request):
    model_list = []
    for pattern in get_resolver('reports.urls').url_patterns:
        if not isinstance(pattern, URLPattern):
            continue
        name = pattern.default_args.get('report_name', None)
        if not name:
            continue
        model_list.append({'name': name, 'url': pattern.pattern})

    return render(request, 'reports_index.html', {
        'user': request.user,
        'title': 'Reports',
        'model_list': model_list
    })
    
@staff_member_required
def regdate_report(request):
    order_model = apps.get_model('reg23', 'Order')

    stats = order_model.objects.filter(
        valid=True
    ).annotate(
        order_date=TruncDate('date')
    ).values('order_date').annotate(
        ticket_count=Count('order_num'),
        total_revenue=Sum('amount')
    ).order_by('order_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="regdate_report_{SCALE_EVENT_DATE.year}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order Date', 'Days Out', 'Tickets', 'Revenue'])
    
    for stat in stats:
        order_date = stat['order_date']
        days_out = (SCALE_EVENT_DATE- order_date).days
        tickets =  stat['ticket_count']
        revenue = stat['total_revenue'] or 0
        writer.writerow([order_date, days_out, tickets, revenue])
        
    return response