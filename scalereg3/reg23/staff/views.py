from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from reg23 import views as reg23_views


@login_required
def index(request):
    return render(request, 'reg_staff_index.html', {'title': 'Staff Page'})


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
