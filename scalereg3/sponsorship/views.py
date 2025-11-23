from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from common import utils

from . import forms
from . import models

STEPS_TOTAL = 5

SPONSOR_COOKIE = 'sponsor'


def render_error(request, error_message):
    return render(request, 'sponsorship_error.html', {
        'title': 'Registration Problem',
        'error_message': error_message,
    })


def check_payment_amount(amount_str, expected_cost):
    actual = int(float(amount_str))
    expected = int(float(expected_cost))
    if actual == 0:
        return HttpResponseServerError(
            f'incorrect payment amount: got {actual}')
    if expected == 0:
        return HttpResponseServerError(
            'incorrect payment amount: should not expect 0')
    if actual == expected:
        return None
    return HttpResponseServerError(
        f'incorrect payment amount: expected {expected}, got {actual}')


def check_sales_request(request, required_vars):
    if request.method != 'POST':
        return HttpResponse(f'Method not allowed: {request.method}',
                            status=405)

    for var in required_vars:
        if var not in request.POST:
            return HttpResponseServerError('required vars missing')
    if request.POST['RESULT'] != '0':
        return HttpResponseServerError('transaction did not succeed')
    if request.POST['RESPMSG'] != 'Approved':
        return HttpResponseServerError('transaction declined')
    return None


def check_vars(request, post):
    if request.method != 'POST':
        return redirect('/sponsorship/')

    for var in post:
        if var not in request.POST:
            return render_error(request, f'No {var} information.')
    return None


def get_pending_order(order_num):
    if models.Order.objects.filter(order_num=order_num):
        return HttpResponseServerError('order already exists')

    try:
        return models.PendingOrder.objects.get(order_num=order_num)
    except models.PendingOrder.DoesNotExist:
        return HttpResponseServerError('cannot get pending order')


def get_posted_items(post, avail_items):
    selected_items = set()
    for i in range(len(avail_items)):
        key = f'item{i}'
        if key in post:
            try:
                item = models.Item.objects.get(name=post[key])
            except models.Item.DoesNotExist:
                continue

            if item in avail_items:
                selected_items.add(item)
    return selected_items


def get_promo_from_request(request_data, avail_promocodes):
    if 'promo' not in request_data:
        return None
    promo = request_data['promo'].upper()
    return promo if promo in avail_promocodes else None


def get_promo_in_use(request_data):
    active_promo_set = models.PromoCode.active_objects
    promo_name = get_promo_from_request(request_data, active_promo_set.names())
    if not promo_name:
        return (None, None)
    return (promo_name, active_promo_set.get(name=promo_name))


def validate_save_sponsor(request, package, items, promo_in_use):
    if SPONSOR_COOKIE in request.session and request.session[SPONSOR_COOKIE]:
        return render_error(request, 'Already added sponsor.')

    form = forms.SponsorForm(request.POST)
    if not form.is_valid():
        return form

    if not request.session.test_cookie_worked():
        return render_error(
            request,
            ('Please do not register multiple sponsors at the same time. ',
             'Please make sure you have cookies enabled.'))

    # create sponsor
    new_sponsor = form.save(commit=False)
    new_sponsor.package = package
    new_sponsor.promo = promo_in_use

    # save sponsor
    new_sponsor.save()
    form.save_m2m()

    # add ordered items
    for item in items:
        new_sponsor.ordered_items.add(item)

    request.session[SPONSOR_COOKIE] = new_sponsor.id

    return redirect('/sponsorship/payment/')


def index(request):
    avail_packages = models.Package.public_objects.order_by('description')

    request_data = {}
    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = request.POST
    (promo_name, promo_in_use) = get_promo_in_use(request_data)
    for package in avail_packages:
        package.apply_promo(promo_in_use)

    request.session.set_test_cookie()

    return render(
        request, 'sponsorship_index.html', {
            'title': 'Sponsorship',
            'packages': avail_packages,
            'promo': promo_name,
            'step': 1,
            'steps_total': STEPS_TOTAL,
        })


def add_items(request):
    required_vars = ['package', 'promo']
    r = check_vars(request, required_vars)
    if r:
        return r

    package_name = request.POST['package']
    try:
        package = models.Package.public_objects.get(name=package_name)
    except models.Package.DoesNotExist:
        return render_error(request, f'Package {package_name} not found.')

    (promo_name, promo_in_use) = get_promo_in_use(request.POST)
    package.apply_promo(promo_in_use)
    items = package.get_items()
    for item in items:
        item.apply_promo(promo_in_use)

    return render(
        request, 'sponsorship_items.html', {
            'title': 'Sponsorship - Add Items',
            'package': package,
            'items': items,
            'promo': promo_name,
            'step': 2,
            'steps_total': STEPS_TOTAL,
        })


def add_sponsor(request):
    required_vars = ['package', 'promo']
    r = check_vars(request, required_vars)
    if r:
        return r

    action = None
    if 'HTTP_REFERER' in request.META:
        if '/sponsorship/add_items/' in request.META['HTTP_REFERER']:
            action = 'add_new'
        elif '/sponsorship/add_sponsor/' in request.META['HTTP_REFERER']:
            action = 'validate'
    if not action:
        return render_error(request, 'Invalid referrer.')

    package_name = request.POST['package']
    try:
        package = models.Package.public_objects.get(name=package_name)
    except models.Package.DoesNotExist:
        return render_error(request, f'Package {package_name} not found.')

    (promo_name, promo_in_use) = get_promo_in_use(request.POST)
    package.apply_promo(promo_in_use)
    items = get_posted_items(request.POST, package.get_items())
    for item in items:
        item.apply_promo(promo_in_use)

    offset_items = [item for item in items if item.package_offset]
    offset_item = offset_items[0] if offset_items else None
    total = package.package_cost(items, None)

    if action == 'add_new':
        request.session[SPONSOR_COOKIE] = ''
        form = forms.SponsorForm()
    else:
        assert action == 'validate'
        result = validate_save_sponsor(request, package, items, promo_in_use)
        if isinstance(result, HttpResponse):
            return result

        assert isinstance(result, forms.SponsorForm)
        form = result

    return render(
        request, 'sponsorship_sponsor.html', {
            'title': 'Register Sponsor',
            'package': package,
            'promo': promo_name,
            'items': items,
            'offset_item': offset_item,
            'total': total,
            'form': form,
            'agreement_url': settings.SCALEREG_SPONSORSHIP_AGREEMENT_URL,
            'step': 3,
            'steps_total': STEPS_TOTAL,
        })


def payment(request):
    if request.method != 'GET':
        return redirect('/sponsorship/')
    sponsor_id = request.session.get(SPONSOR_COOKIE, None)
    if not isinstance(sponsor_id, int):
        return redirect('/sponsorship/')

    sponsor = None
    try:
        sponsor = models.Sponsor.objects.get(id=sponsor_id)
    except models.Sponsor.DoesNotExist:
        pass

    if not sponsor or sponsor.valid:
        return render_error(request, 'No sponsor to pay for.')

    order_num = None
    order_tries = 0
    while True:
        existing_order_ids = [
            x.order_num for x in models.PendingOrder.objects.all()
        ]
        existing_order_ids += [x.order_num for x in models.Order.objects.all()]
        order_num = utils.generate_unique_id(10, existing_order_ids)
        pending_order = models.PendingOrder(order_num=order_num,
                                            sponsor=sponsor)
        try:
            pending_order.save()
            break
        except IntegrityError:
            order_tries += 1
            if order_tries > 10:
                return render_error(request, 'cannot generate order ID')

    return render(
        request, 'sponsorship_payment.html', {
            'title': 'Sponsorship - Payment',
            'sponsor': sponsor,
            'order': order_num,
            'payflow_url': settings.SCALEREG_PAYFLOW_URL,
            'payflow_partner': settings.SCALEREG_PAYFLOW_PARTNER,
            'payflow_login': settings.SCALEREG_PAYFLOW_LOGIN,
            'step': 4,
            'steps_total': STEPS_TOTAL,
        })


@csrf_exempt
def sale(request):
    required_vars = [
        'NAME',
        'ADDRESS',
        'CITY',
        'STATE',
        'ZIP',
        'COUNTRY',
        'PHONE',
        'EMAIL',
        'AMOUNT',
        'AUTHCODE',
        'PNREF',
        'RESULT',
        'RESPMSG',
        'USER1',
    ]
    r = check_sales_request(request, required_vars)
    if r:
        return r

    maybe_pending_order = get_pending_order(request.POST['USER1'])
    if isinstance(maybe_pending_order, HttpResponseServerError):
        return maybe_pending_order

    sponsor = maybe_pending_order.sponsor
    r = check_payment_amount(request.POST['AMOUNT'], sponsor.package_cost())
    if r:
        return r

    try:
        order = models.Order(order_num=request.POST['USER1'],
                             valid=True,
                             name=request.POST['NAME'],
                             address=request.POST['ADDRESS'],
                             city=request.POST['CITY'],
                             state=request.POST['STATE'],
                             zip_code=request.POST['ZIP'],
                             country=request.POST['COUNTRY'],
                             email=request.POST['EMAIL'],
                             phone=request.POST['PHONE'],
                             amount=request.POST['AMOUNT'],
                             payflow_auth_code=request.POST['AUTHCODE'],
                             payflow_pnref=request.POST['PNREF'],
                             payflow_resp_msg=request.POST['RESPMSG'],
                             payflow_result=request.POST['RESULT'],
                             sponsor=sponsor,
                             already_paid_sponsor=sponsor.valid)
        order.save()
    except IntegrityError:
        return HttpResponseServerError('cannot save order')

    if not sponsor.valid:
        sponsor.valid = True
        sponsor.save()

    return HttpResponse('success')


@csrf_exempt
def failed_payment(request):
    return render(request, 'sponsorship_failed.html', {
        'title': 'Sponsorship Payment Failed',
    })


@csrf_exempt
def finish_payment(request):
    required_vars = (
        'NAME',
        'EMAIL',
        'AMOUNT',
        'USER1',
    )
    r = check_vars(request, required_vars)
    if r:
        return r

    try:
        order = models.Order.objects.get(order_num=request.POST['USER1'])
    except models.Order.DoesNotExist:
        return render_error(request, 'Your sponsorship order cannot be found')

    return render(
        request, 'sponsorship_receipt.html', {
            'title': 'Sponsorship Payment Receipt',
            'name': request.POST['NAME'],
            'email': request.POST['EMAIL'],
            'sponsor': order.sponsor,
            'already_paid_sponsor': order.already_paid_sponsor,
            'order': request.POST['USER1'],
            'step': 5,
            'steps_total': STEPS_TOTAL,
            'total': request.POST['AMOUNT'],
        })
