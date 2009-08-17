from django.conf import settings
from django.forms.util import ErrorList
from django.http import HttpResponse
from django.shortcuts import render_to_response
from scalereg.simple_cfp import forms
from scalereg.simple_cfp import models
from scalereg.common import utils

if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
  from django.core.mail import send_mail
  import smtplib

if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
  from recaptcha.client.captcha import displayhtml
  from recaptcha.client.captcha import submit

class ErrorMsg:
  # Common messages
  CAPTCHA_SERVER_ERROR = 'Could not contact reCAPTCHA server'
  EMAIL_ERROR = 'Could not send email'
  # SubmitPresentation
  INVALID_CODE = 'Invalid speaker code'
  INVALID_EMAIL = 'Contact email does not match speaker code'


def GenerateRecaptchaHTML(request, error_code=None):
  if not settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
    return ''
  return displayhtml(settings.RECAPTCHA_PUBLIC_KEY, request.is_secure(),
                     error_code)


def GeneratePresentationValidationCode():
  submission_codes = [
    p.submission_code for p in models.Presentation.objects.all()]
  return utils.GenerateUniqueID(10, submission_codes)


def GenerateSpeakerValidationCode():
  speaker_ids = [s.validation_code for s in models.Speaker.objects.all()]
  return utils.GenerateUniqueID(10, speaker_ids)


def SendValidationEmail(speaker):
  if not settings.SCALEREG_SIMPLECFP_SEND_MAIL:
    return False
  try:
    send_mail("Your simple_cfp validation code",
              "Your simple_cfp validation code is %s" % speaker.validation_code,
              settings.SCALEREG_EMAIL,
              [speaker.contact_email])
    return True
  except smtplib.SMTPException:
    return False


def index(request):
  return render_to_response('simple_cfp/cfp_index.html',
    {'title': 'Simple CFP',
     'send_email': settings.SCALEREG_SIMPLECFP_SEND_MAIL,
    })


def RecoverValidation(request):
  TITLE = 'Recover Validation Code'

  if not settings.SCALEREG_SIMPLECFP_SEND_MAIL:
    return HttpResponse()

  if request.method == 'POST':
    if 'email' in request.POST:
      email = request.POST['email']
    else:
      email = ''

    if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
      try:
        recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                    request.POST['recaptcha_response_field'],
                                    settings.RECAPTCHA_PRIVATE_KEY,
                                    request.META['REMOTE_ADDR'])
      except:
        return render_to_response('simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return render_to_response('simple_cfp/cfp_recover_validation.html',
          {'title': TITLE,
           'email': email,
           'recaptcha_html': recaptcha_html,
          })

    speakers = models.Speaker.objects.filter(contact_email=email)
    speakers = speakers.filter(valid=True)
    if not speakers:
      return render_to_response('simple_cfp/cfp_recover_validation.html',
        {'title': TITLE,
         'email': email,
         'error': True,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if not SendValidationEmail(speakers[0]):
      return render_to_response('simple_cfp/cfp_error.html',
        {'title': TITLE,
         'error_message': ErrorMsg.EMAIL_ERROR,
        })
    return render_to_response('simple_cfp/cfp_recover_validation.html',
      {'title': TITLE,
       'email': email,
       'sent': True,
      })
  else:
    return render_to_response('simple_cfp/cfp_recover_validation.html',
      {'title': TITLE,
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })


def RegisterSpeaker(request):
  TITLE = 'Register Speaker'

  if request.method == 'POST':
    form = forms.SpeakerForm(request.POST)
    if not form.is_valid():
      return render_to_response('simple_cfp/cfp_speaker.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
      try:
        recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                    request.POST['recaptcha_response_field'],
                                    settings.RECAPTCHA_PRIVATE_KEY,
                                    request.META['REMOTE_ADDR'])
      except:
        return render_to_response('simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return render_to_response('simple_cfp/cfp_speaker.html',
          {'title': TITLE,
           'form': form,
           'recaptcha_html': recaptcha_html,
          })

    new_speaker = form.save(commit=False)
    new_speaker.validation_code = GenerateSpeakerValidationCode()
    new_speaker = form.save()

    return render_to_response('simple_cfp/cfp_speaker_registered.html',
      {'title': TITLE,
       'speaker': new_speaker,
      })
  else:
    return render_to_response('simple_cfp/cfp_speaker.html',
      {'title': TITLE,
       'form': forms.SpeakerForm(),
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })


def SubmitPresentation(request):
  TITLE = 'Submit Presentation'

  if request.method == 'POST':
    form = forms.PresentationForm(request.POST)
    if not form.is_valid():
      return render_to_response('simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    try:
      speaker = models.Speaker.objects.get(
          validation_code=form.cleaned_data['speaker_code'])
    except models.Speaker.DoesNotExist:
      form.errors['speaker_code'] = ErrorList([ErrorMsg.INVALID_CODE])
      return render_to_response('simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if speaker.contact_email != form.cleaned_data['contact_email']:
      form.errors['contact_email'] = ErrorList([ErrorMsg.INVALID_EMAIL])
      return render_to_response('simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
      try:
        recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                    request.POST['recaptcha_response_field'],
                                    settings.RECAPTCHA_PRIVATE_KEY,
                                    request.META['REMOTE_ADDR'])
      except:
        return render_to_response('simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return render_to_response('simple_cfp/cfp_presentation.html',
          {'title': TITLE,
           'form': form,
           'recaptcha_html': recaptcha_html,
          })

    new_presentation = form.save(commit=False)
    new_presentation.speaker = speaker
    new_presentation.submission_code = GeneratePresentationValidationCode()
    new_presentation = form.save()
    form.save_m2m()

    return render_to_response('simple_cfp/cfp_presentation_submitted.html',
      {'title': TITLE,
       'presentation': new_presentation,
      })
  else:
    return render_to_response('simple_cfp/cfp_presentation.html',
      {'title': TITLE,
       'form': forms.PresentationForm(),
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })
