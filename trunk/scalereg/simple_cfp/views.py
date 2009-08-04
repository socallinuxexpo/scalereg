from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from scalereg.simple_cfp import forms
from scalereg.simple_cfp import models
from scalereg.common import utils
import datetime

if settings.USE_RECAPTCHA:
  from recaptcha.client.captcha import displayhtml
  from recaptcha.client.captcha import submit

def GenerateRecaptchaHTML(request, error_code=None):
  if not settings.USE_RECAPTCHA:
    return ''
  return displayhtml(settings.RECAPTCHA_PUBLIC_KEY, request.is_secure(),
                     error_code)


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
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if settings.USE_RECAPTCHA:
      try:
        recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                    request.POST['recaptcha_response_field'],
                                    settings.RECAPTCHA_PRIVATE_KEY,
                                    request.META['REMOTE_ADDR'])
      except:
        return render_to_response('simple_cfp/cfp_error.html',
          {'title': title,
           'error_message': 'Could not contact reCAPTCHA server.',
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return render_to_response('simple_cfp/cfp_speaker.html',
          {'title': title,
           'form': form,
           'recaptcha_html': recaptcha_html,
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
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })
