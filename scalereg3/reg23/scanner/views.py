import urllib.parse

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render

from reg23 import views as reg23_views


@login_required
def index(request):
    if request.method != 'GET':
        return HttpResponse(f'Method not allowed: {request.method}',
                            status=405)

    response = ''
    color = 'red'
    if 'RESULT' in request.GET and 'SIZE' in request.GET:
        attendee = None
        result = urllib.parse.unquote(request.GET['RESULT']).split('~')
        if result:
            attendee = reg23_views.get_attendee_for_id(result[0][:-1])

        if attendee:
            if reg23_views.get_attendee_parity_code(attendee) != result[0][-1]:
                response = 'Invalid parity bit'
            elif not attendee.valid or not attendee.order:
                response = 'Invalid attendee'
            elif not attendee.checked_in:
                response = 'Attendee not checked in'
        else:
            response = 'Invalid barcode'

        if not response:
            if attendee.tshirt:
                response = f'Badge already scanned: {attendee.id}'
                color = 'orange'
            else:
                attendee.tshirt = request.GET['SIZE']
                try:
                    attendee.save()
                    response = f'Scanned {attendee.id}'
                    color = 'green'
                except IntegrityError:
                    response = 'Database error'

    return render(request, 'reg_scanner_index.html', {
        'color': color,
        'response': response,
    })
