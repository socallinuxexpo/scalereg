from django.shortcuts import render

from . import models

STEPS_TOTAL = 5


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
