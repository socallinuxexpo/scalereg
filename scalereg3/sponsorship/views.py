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


def index(request):
    avail_packages = models.Package.public_objects.order_by('description')

    request.session.set_test_cookie()

    return render(
        request, 'sponsorship_index.html', {
            'title': 'Sponsorship',
            'packages': avail_packages,
            'step': 1,
            'steps_total': STEPS_TOTAL,
        })


def add_items(request):
    required_vars = ['package']
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

    items = package.get_items()

    return render(
        request, 'sponsorship_items.html', {
            'title': 'Sponsorship - Add Items',
            'package': package,
            'items': items,
            'step': 2,
            'steps_total': STEPS_TOTAL,
        })
