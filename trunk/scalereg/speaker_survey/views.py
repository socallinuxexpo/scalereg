# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from scalereg.common.validators import ScaleValidationError
from scalereg.reg6 import models as reg6models
from scalereg.speaker_survey import forms
from scalereg.speaker_survey import models
from scalereg.speaker_survey import validators

def Survey(request, hashval=None, id=None):
  try:
    validators.isValid7XHash(hashval, None)
  except ScaleValidationError:
    raise
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
      'error_message': 'Invalid Survey URL',
      })

  if not id:
    return SurveyIndex(hashval)

  speaker = None
  try:
    speaker = models.Speaker.objects.get(id=id)

    if request.method == 'POST':
      return SurveyFill(hashval, speaker, request.POST)
  except models.Speaker.DoesNotExist:
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
       'error_message': 'Cannot find speaker',
      })
  try:
    s = models.Survey7X.objects.filter(hash=hashval).get(speaker=speaker)
    return SurveyView(s)
  except models.Survey7X.DoesNotExist:
    return SurveyFill(hashval, speaker)


def SurveyIndex(hashval):
  surveys = models.Survey7X.objects.filter(hash=hashval)
  new_speakers = models.Speaker.objects.all().order_by('name')
  old_speakers = []
  for s in surveys:
    new_speakers = new_speakers.exclude(id=s.speaker.id)
    old_speakers.append(s.speaker)

  return render_to_response('speaker_survey/survey_index.html',
    {'title': 'Speaker Surveys',
     'new': new_speakers,
     'old': old_speakers,
    })


def SurveyFill(hashval, speaker, post_data=None):
  if not post_data:
    form = forms.Survey7XForm()
  else:
    try:
      # work around DB integrity error for duplicates
      survey = models.Survey7X.objects.filter(hash=hashval)
      survey = survey.get(speaker=speaker)
      return SurveyView(survey)
    except models.Survey7X.DoesNotExist:
      pass

    form = forms.Survey7XForm(post_data)
    if form.is_valid():
      new_survey = form.save(commit=False)
      new_survey.hash = hashval
      new_survey.speaker = speaker
      new_survey.save()
      form.save_m2m()
      return SurveyView(new_survey)

  return render_to_response('speaker_survey/survey_fill.html',
    {'title': 'Speaker Surveys',
     'form': form,
     'kiosk': False, # Not sure why I have to add this for Stu's server
     'messages': None, # Not sure why I have to add this for Stu's server
     'speaker': speaker,
     'survey': models.Survey7X(),
    })


def SurveyView(s):
  if not s:
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
       'error_message': 'Cannot find survey',
      })

  return render_to_response('speaker_survey/survey_view.html',
    {'title': 'Speaker Surveys',
     'survey': s,
    })


def SurveyLookup(request):
  if request.method == 'GET':
    return render_to_response('speaker_survey/survey_lookup.html',
      {'title': 'Speaker Surveys',
       'unknown': False,
      })
  else:
    error = False
    hashval = None
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
        if attendee.checked_in and attendee.first_name == request.POST['name']:
          hashval = validators.hashAttendee(attendee) + '%04d' % id
      except reg6models.Attendee.DoesNotExist:
        error = True

    if hashval:
      return render_to_response('speaker_survey/survey_lookup.html',
        {'title': 'Speaker Surveys',
         'hash': hashval,
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
    try:
      speaker.save()
    except:
      response.write('bad entry: %s<br />\n' % invalid)
      continue
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
    hashval = validators.hashval(f.first_name + f.last_name)[:6]
    hashval += '%04d' % f.id
    response.write('%s %s\n' % (f.first_name, f.last_name))
    response.write('%s\n' % f.email)
    response.write('%s\n' % hashval)
  return response


def GetScore(score_choice):
  if score_choice == '0sd':
    return -2
  elif score_choice == '1di':
    return -1
  elif score_choice == '2ne':
    return 0
  elif score_choice == '3ag':
    return 1
  elif score_choice == '4sa':
    return 2
  else:
    raise ValueError(score_choice)


def ScoreTotal(speakers):
  scores = []
  for sp in speakers:
    surveys = models.Survey7X.objects.filter(speaker=sp)
    num = surveys.count()
    if num == 0:
      sp.score1 = 'N/A'
      sp.score2 = 'N/A'
      sp.num = 0
      continue

    sc1 = 0
    sc2 = 0
    for sv in surveys:
      sc1 = sum( [ GetScore(getattr(sv, 'q%02d' % i)) for i in xrange(0, 7) ] )
      sc2 = sum( [ GetScore(getattr(sv, 'q%02d' % i)) for i in xrange(7, 15) ] )
    sp.score1 = round(float(sc1) / num, 1)
    sp.score2 = round(float(sc2) / num, 1)
    sp.num = num


def ScoreSurveys(surveys):
  scores = []
  comments = []
  for i in xrange(0, 15):
    scores.append([0, 0, 0, 0, 0, 0])

  num = surveys.count()

  sc1 = 0
  sc2 = 0
  for sv in surveys:
    if sv.comments:
      comments.append(sv.comments)

    for i in xrange(0, 7):
      s = getattr(sv, 'q%02d' % i)
      scores[i][int(s[0])] += 1
      sc1 += GetScore(s)
    for i in xrange(7, 15):
      s = getattr(sv, 'q%02d' % i)
      scores[i][int(s[0])] += 1
      sc2 += GetScore(s)
  for i in xrange(0, 15):
    total = sum([GetScore(models.VALUE_CHOICES[j][0]) * scores[i][j]
                 for j in xrange(0,5)])
    scores[i][5] = round(float(total) / num, 1)
  help_text = surveys[0].help_text()
  for i in xrange(0, 15):
    scores[i].insert(0, help_text[i])

  sc1 = round(float(sc1) / num, 1)
  sc2 = round(float(sc2) / num, 1)
  return (scores, sc1, sc2, num, comments)


@login_required
def Scores(request, id=None):
  if not request.user.is_staff:
    return HttpResponse('')
  if not id:
    speakers = models.Speaker.objects.all().order_by('name')
    ScoreTotal(speakers)
    return render_to_response('speaker_survey/scores_index.html',
      {'title': 'Speaker Scores',
       'speakers': speakers,
      })

  speaker = None
  try:
    speaker = models.Speaker.objects.get(id=id)
  except models.Speaker.DoesNotExist:
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
       'error_message': 'Cannot find speaker',
      })
  surveys = models.Survey7X.objects.filter(speaker=speaker)
  if not surveys:
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
       'error_message': 'Speaker has no filled survey response',
      })

  scores, sc1, sc2, num, comments = ScoreSurveys(surveys)
  return render_to_response('speaker_survey/scores_speaker.html',
    {'title': 'Speaker Scores',
     'speaker': speaker,
     'scores': scores,
     'sc1': sc1,
     'sc2': sc2,
     'num': num,
     'comments': comments,
     'choices': [ x[1] for x in models.VALUE_CHOICES ],
    })
