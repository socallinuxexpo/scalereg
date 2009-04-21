# Create your views here.

from django.shortcuts import render_to_response
from scale.reg6 import models as reg6models
from scale.speaker_survey import validators

def SurveyLookup(request):
  if request.method == 'GET':
    return render_to_response('speaker_survey/survey_lookup.html',
      {'title': 'Speaker Surveys',
       'unknown': False,
      })
  else:
    error = False
    hash = None
    id = -1
    if 'name' not in request.POST or 'id' not in request.POST:
      error = True
    if not error:
      try:
        id = int(request.POST['id'])
      except ValueError:
        error = True

    if not error:
      try:
        attendee = reg6models.Attendee.objects.get(id=id)
        if attendee.first_name == request.POST['name']:
          hash = validator.hash(attendee.first_name + attendee.last_name)[:6]
          hash += '%04d' % id
      except reg6models.Attendee.DoesNotExist:
        error = True

    if hash:
      return render_to_response('speaker_survey/survey_lookup.html',
        {'title': 'Speaker Surveys',
         'hash': hash,
        })
    else:
      return render_to_response('speaker_survey/survey_lookup.html',
        {'title': 'Speaker Surveys',
         'id': request.POST['id'],
         'name': request.POST['name'],
         'unknown': True,
        })
