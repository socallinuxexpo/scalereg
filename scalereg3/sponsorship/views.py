from django.shortcuts import redirect
from django.shortcuts import render

from . import models

STEPS_TOTAL = 5


def check_vars(request, post):
    if request.method != 'POST':
        return redirect('/sponsorship/')

    for var in post:
        if var not in request.POST:
            return render(
                request, 'sponsorship_error.html', {
                    'title': 'Registration Problem',
                    'error_message': f'No {var} information.',
                })
    return None


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
        return render(
            request, 'sponsorship_error.html', {
                'title': 'Registration Problem',
                'error_message': f'Package {package_name} not found.',
            })

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
