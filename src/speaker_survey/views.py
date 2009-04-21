# Create your views here.

from django.shortcuts import render_to_response

def SurveyLookup(request):
  if request.method == 'GET':
    return render_to_response('speaker_survey/survey_lookup.html',
      {'title': 'Speaker Surveys',
       'unknown': False,
      })
  else:
    return render_to_response('speaker_survey/error.html',
      {'title': 'Survey Error',
       'error_message': 'Invalid Operation',
      })
