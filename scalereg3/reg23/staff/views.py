from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db import transaction
from django.shortcuts import render

from reg23 import forms as reg23_forms
from reg23 import models as reg23_models
from reg23 import views as reg23_views


def get_attendee_from_express_check_in_code(code):
    code = code.strip().lower()
    if len(code) != 10:
        return None

    attendee = reg23_views.get_attendee_for_id(code[:4])
    return attendee if attendee and attendee.checkin_code() == code else None


@login_required
def index(request):
    return render(request, 'reg_staff_index.html', {'title': 'Staff Page'})


@login_required
def cash_payment(request):
    tickets = reg23_models.Ticket.objects.filter(cash=True)
    if request.method == 'GET':
        return render(
            request, 'reg_staff_cash_payment.html', {
                'title': 'Cash Payment',
                'form': reg23_forms.AttendeeCashForm(),
                'tickets': tickets,
            })

    required_vars = ['TICKET']
    r = reg23_views.check_vars(request, required_vars)
    if r:
        return r

    try:
        ticket = tickets.get(name=request.POST['TICKET'])
    except reg23_models.Ticket.DoesNotExist:
        return render(
            request, 'reg_staff_cash_payment.html', {
                'title': 'Cash Payment',
                'error_message': 'Cannot find ticket type',
                'tickets': tickets,
            })

    form = reg23_forms.AttendeeCashForm(request.POST)
    if not form.is_valid():
        return render(request, 'reg_staff_cash_payment.html', {
            'title': 'Cash Payment',
            'form': form,
            'tickets': tickets,
        })

    attendee = form.save(commit=False)
    attendee.badge_type = ticket
    attendee.valid = True
    attendee.checked_in = True

    order_num = reg23_views.generate_order_id(
        reg23_views.get_existing_order_ids())
    attendee.order = reg23_models.Order(order_num=order_num,
                                        valid=True,
                                        name=attendee.full_name(),
                                        address='Cash',
                                        city='Cash',
                                        state='Cash',
                                        zip_code=attendee.zip_code,
                                        email=attendee.email,
                                        amount=ticket.price,
                                        payment_type='cash')

    try:
        with transaction.atomic():
            attendee.save()
            form.save_m2m()
            attendee.order.save()
    except IntegrityError:
        return render(
            request, 'reg_staff_cash_payment.html', {
                'title': 'Cash Payment',
                'tickets': tickets,
                'error_message': 'Cannot save order, bad data?',
            })

    return render(
        request, 'reg_staff_cash_payment.html', {
            'title': 'Cash Payment',
            'attendee': attendee,
            'form': reg23_forms.AttendeeCashForm(),
            'tickets': tickets,
        })


@login_required
def check_in(request):
    if request.method == 'GET':
        return render(request, 'reg_staff_check_in.html', {
            'title': 'Attendee Check In',
        })

    attendees = []
    if 'express' in request.POST:
        attendee = get_attendee_from_express_check_in_code(
            request.POST['express'])
        if attendee:
            attendees.append(attendee)

    if not attendees and 'payflow' in request.POST and request.POST['payflow']:
        orders = reg23_models.Order.objects.filter(
            payment_type='payflow', payflow_pnref=request.POST['payflow'])
        if orders.count() == 1:
            attendees = list(
                reg23_models.Attendee.objects.filter(order=orders[0]))

    if not attendees and 'last_name' in request.POST and request.POST[
            'last_name']:
        attendees = list(
            reg23_models.Attendee.objects.filter(
                last_name__icontains=request.POST['last_name']).order_by(
                    '-valid'))

    if not attendees and 'zip_code' in request.POST and request.POST[
            'zip_code']:
        attendees = list(
            reg23_models.Attendee.objects.filter(
                zip_code=request.POST['zip_code']))

    return render(
        request, 'reg_staff_check_in.html', {
            'title': 'Attendee Check In',
            'attendees': attendees,
            'express': request.POST['express'],
            'last_name': request.POST['last_name'],
            'payflow': request.POST['payflow'],
            'search': True,
            'zip_code': request.POST['zip_code'],
        })


@login_required
def receipt(request):
    attendee = None
    error_message = None
    if request.method == 'POST' and 'attendee' in request.POST:
        attendee = reg23_views.get_attendee_for_id(request.POST['attendee'])
        if attendee:
            if (not attendee.valid or not attendee.order
                    or not attendee.order.valid):
                attendee = None
                error_message = 'Invalid attendee'
        else:
            error_message = 'Attendee not found'
    return render(
        request, 'reg_staff_receipt.html', {
            'title': 'Receipt lookup',
            'attendee': attendee,
            'error_message': error_message,
        })
