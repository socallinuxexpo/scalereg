# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from scale.reg6 import models as reg6models
from scale.speaker_survey import models
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


@login_required
def MassAdd(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  if request.method == 'GET':
    response = HttpResponse()
    response.write('<html><head></head><body><form method="post">')
    response.write('<textarea name="data" rows="25" cols="80"></textarea>')
    response.write('<br /><input type="submit" /></form>')
    response.write('</body></html>')
    return response

  if 'data' not in request.POST:
    return HttpResponse('No Data')

  response = HttpResponse()
  response.write('<html><head></head><body>')

  data = request.POST['data'].split('\n')
  print data
  while data:
    name = data.pop(0).strip()
    title = data.pop(0).strip()
    url = data.pop(0).strip()
    if not name or not title:
      print 'blah'
      continue

    speaker = models.Speaker()
    speaker.name = name
    speaker.title = title
    speaker.url = url
    invalid = speaker.validate()
    if invalid:
      response.write('bad entry: %s<br />\n' % invalid)
      continue
    speaker.save()
    response.write('Added %s<br />\n' % speaker)

  response.write('</body></html>')
  return response


@login_required
def UrlDump(request):
  if not request.user.is_superuser:
    return HttpResponse('')
  attendees = reg6models.Attendee.objects.filter(checked_in=True)
  response = HttpResponse(mimetype='text/plain')
  for f in attendees:
    hash = validator.hash(f.first_name + f.last_name)[:6]
    hash += '%04d' % f.id
    response.write('%s %s\n' % (f.first_name, f.last_name))
    response.write('%s\n' % f.email)
    response.write('%s\n' % hash)
  return response
