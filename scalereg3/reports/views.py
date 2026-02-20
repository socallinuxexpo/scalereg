import csv
import io
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


def get_addon_data():
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_30 = today - timezone.timedelta(days=30)
    days_7 = today - timezone.timedelta(days=7)

    attendee_model = apps.get_model('reg23', 'Attendee')
    item_model = apps.get_model('reg23', 'Item')

    valid_attendees = attendee_model.objects.filter(valid=True)

    addon_data = []
    for item in item_model.objects.filter(active=True).order_by('name'):
        attendees_with_addon = valid_attendees.filter(ordered_items=item)

        data = {
            'name':
            item.description,
            'code':
            item.name,
            'numbers':
            attendees_with_addon.count(),
            'numbers_30':
            attendees_with_addon.filter(order__date__gt=days_30).count(),
            'numbers_7':
            attendees_with_addon.filter(order__date__gt=days_7).count(),
        }
        addon_data.append(data)

    return addon_data


@staff_member_required
def sales_dashboard(request, report_name):
    return render(request, 'reports_sales_dashboard.html', {
        'title': report_name,
        'orders': get_orders_data(),
        'addons': get_addon_data(),
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
def regdate_report(request, report_name):
    order_model = apps.get_model('reg23', 'Order')

    stats = order_model.objects.filter(valid=True).annotate(
        order_date=TruncDate('date')).values('order_date').annotate(
            ticket_count=Count('order_num'),
            total_revenue=Sum('amount')).order_by('order_date')

    # Build CSV content
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['date', 'days out from scale', 'tickets', 'revenue'])

    for stat in stats:
        order_date = stat['order_date']
        days_out = (SCALE_EVENT_DATE - order_date).days
        tickets = stat['ticket_count']
        revenue = stat['total_revenue'] or 0
        writer.writerow([order_date, days_out, tickets, revenue])

    csv_content = csv_buffer.getvalue()

    # Check if the user requested a CSV download
    if request.GET.get('download') == 'true':
        response = HttpResponse(csv_content, content_type='text/csv')
        response[
            'Content-Disposition'] = 'attachment; filename="regdate_report.csv"'
        return response

    return render(request, 'reports_regdate.html', {
        'title': report_name,
        'csv_content': csv_content
    })
