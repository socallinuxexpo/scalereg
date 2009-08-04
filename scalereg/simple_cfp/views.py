from django.http import HttpResponse
from django.shortcuts import render_to_response
from scalereg.simple_cfp import forms
from scalereg.simple_cfp import models
from scalereg.common import utils
import datetime

def GenerateSpeakerValidationCode():
  speaker_ids = [s.validation_code for s in models.Speaker.objects.all()]
  return utils.GenerateUniqueID(10, speaker_ids)


def index(request):
  return HttpResponse('Ok')


def RegisterSpeaker(request):
  title = 'Register Speaker'

  if request.method == 'POST':
    form = forms.SpeakerForm(request.POST)
    if not form.is_valid():
      return render_to_response('simple_cfp/cfp_speaker.html',
        {'title': title,
         'form': form,
        })

    new_speaker = form.save(commit=False)
    new_speaker.valid = False
    new_speaker.validation_code = GenerateSpeakerValidationCode()
    new_speaker.signup_date = datetime.datetime.now()
    new_speaker = form.save()

    return render_to_response('simple_cfp/cfp_speaker_registered.html',
    {'title': title,
     'speaker': new_speaker,
    })

  else:
    return render_to_response('simple_cfp/cfp_speaker.html',
      {'title': title,
       'form': forms.SpeakerForm(),
      })
