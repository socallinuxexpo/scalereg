from django.conf import settings
from django.forms.util import ErrorList
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from scalereg.simple_cfp import forms
from scalereg.simple_cfp import models
from scalereg.common import utils

if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
  from django.core.mail import send_mail
  from django.core.mail import BadHeaderError
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
  # SubmissionStatus
  DELETE_SUCCESS = 'Presentation successfully deleted'
  DELETE_FAIL = 'Could not delete presentation'
  UPLOAD_SUCCESS = 'Presentation successfully uploaded'
  UPLOAD_FAIL = 'Could not upload presentation'


class Cookies:
  CFP_LOGIN = 'cfp_login'


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


def SendConfirmationEmail(presentation):
  if not settings.SCALEREG_SIMPLECFP_SEND_MAIL:
    return False
  try:
    send_mail('Your simple_cfp submission',
              '''Your presentation: %s has been submitted.
Your simple_cfp submission code is %s''' % \
              (presentation.title, presentation.submission_code),
              settings.SCALEREG_SIMPLECFP_EMAIL,
              [presentation.speaker.contact_email])
    return True
  except BadHeaderError:
    # Unlikely to happen, SCALEREG_SIMPLECFP_EMAIL set incorrectly?
    return False
  except smtplib.SMTPException:
    return False


def SendValidationEmail(speaker):
  if not settings.SCALEREG_SIMPLECFP_SEND_MAIL:
    return False
  try:
    send_mail('Your simple_cfp validation code',
              '''Your simple_cfp validation code is %s.
If this email was sent to you by mistake, please reply and let us know.''' % \
              speaker.validation_code,
              settings.SCALEREG_SIMPLECFP_EMAIL,
              [speaker.contact_email])
    return True
  except BadHeaderError:
    # Unlikely to happen, SCALEREG_SIMPLECFP_EMAIL set incorrectly?
    return False
  except smtplib.SMTPException:
    return False


def cfp_render_to_response(request, template, vars):
  if request.session.get(Cookies.CFP_LOGIN):
    vars['logged_in'] = True
  vars['send_email'] = settings.SCALEREG_SIMPLECFP_SEND_MAIL
  return render_to_response(template, vars)


def index(request):
  return cfp_render_to_response(request,
    'simple_cfp/cfp_index.html',
    {'title': 'Simple CFP',
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
        return cfp_render_to_response(request,
          'simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return cfp_render_to_response(request,
          'simple_cfp/cfp_recover_validation.html',
          {'title': TITLE,
           'email': email,
           'recaptcha_html': recaptcha_html,
          })

    speakers = models.Speaker.objects.filter(contact_email=email)
    speakers = speakers.filter(valid=True)
    if not speakers:
      return cfp_render_to_response(request,
        'simple_cfp/cfp_recover_validation.html',
        {'title': TITLE,
         'email': email,
         'error': True,
         'recaptcha_html': GenerateRecaptchaHTML(request),
        })

    if not SendValidationEmail(speakers[0]):
      return cfp_render_to_response(request,
        'simple_cfp/cfp_error.html',
        {'title': TITLE,
         'error_message': ErrorMsg.EMAIL_ERROR,
        })
    return cfp_render_to_response(request,
      'simple_cfp/cfp_recover_validation.html',
      {'title': TITLE,
       'email': email,
       'sent': True,
      })
  else:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_recover_validation.html',
      {'title': TITLE,
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })


def RegisterSpeaker(request):
  TITLE = 'Register Speaker'

  if request.method == 'POST':
    form = forms.SpeakerForm(request.POST)
    if not form.is_valid():
      return cfp_render_to_response(request,
        'simple_cfp/cfp_speaker.html',
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
        return cfp_render_to_response(request,
          'simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return cfp_render_to_response(request,
          'simple_cfp/cfp_speaker.html',
          {'title': TITLE,
           'form': form,
           'recaptcha_html': recaptcha_html,
          })

    new_speaker = form.save(commit=False)
    new_speaker.validation_code = GenerateSpeakerValidationCode()
    new_speaker = form.save()

    email_sent = False
    if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
      email_sent = SendValidationEmail(new_speaker)

    return cfp_render_to_response(request,
      'simple_cfp/cfp_speaker_registered.html',
      {'title': TITLE,
       'email_sent': email_sent,
       'speaker': new_speaker,
      })
  else:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_speaker.html',
      {'title': TITLE,
       'form': forms.SpeakerForm(),
       'recaptcha_html': GenerateRecaptchaHTML(request),
      })


def SubmissionStatus(request):
  TITLE = 'Submission Status'

  email = request.REQUEST.get('email')
  code = request.REQUEST.get('code')
  if not (email and code):
    try:
      (email, code) = request.session[Cookies.CFP_LOGIN]
    except:
      pass

  if not (email and code):
    return cfp_render_to_response(request,
      'simple_cfp/cfp_submission_status.html',
      {'title': TITLE,
      })

  speaker = None
  try:
    speaker = models.Speaker.objects.get(contact_email=email)
    if speaker.validation_code != code:
      speaker = None
  except models.Speaker.DoesNotExist:
    pass

  if not speaker:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_submission_status.html',
      {'title': TITLE,
       'error': ErrorMsg.INVALID_EMAIL,
      })

  presentations = models.Presentation.objects.filter(speaker=speaker)
  request.session[Cookies.CFP_LOGIN] = (email, code)

  # Handle new uploads and deletes
  error = ''
  if request.method == 'POST':
    if 'presentation' in request.POST:
      error = ErrorMsg.UPLOAD_SUCCESS
      try:
        upload_p = presentations.get(id=request.POST['presentation'])
        form = forms.PresentationForm(request.POST, request.FILES)
        if 'file' in form.files:
          form_file = form.files['file']
          upload_p.file.save(form_file.name, form_file)
        else:
          error = ErrorMsg.UPLOAD_FAIL
      except models.Presentation.DoesNotExist:
        error = ErrorMsg.UPLOAD_FAIL
    elif 'delete' in request.POST:
      error = ErrorMsg.DELETE_SUCCESS
      try:
        delete_p = presentations.get(id=request.POST['delete'])
        delete_p.file = None
        delete_p.save()
      except models.Presentation.DoesNotExist:
        error = ErrorMsg.DELETE_FAIL

  return cfp_render_to_response(request,
    'simple_cfp/cfp_submission_status.html',
    {'title': TITLE,
     'code': code,
     'email': email,
     'error': error,
     'presentations': presentations,
     'speaker': speaker,
     'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
    })


def SubmitPresentation(request):
  TITLE = 'Submit Presentation'

  if request.method == 'POST':
    if settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD:
      form = forms.PresentationForm(request.POST, request.FILES)
    else:
      form = forms.PresentationForm(request.POST)
    if not form.is_valid():
      return cfp_render_to_response(request,
        'simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    try:
      speaker = models.Speaker.objects.get(
          validation_code=form.cleaned_data['speaker_code'])
    except models.Speaker.DoesNotExist:
      form.errors['speaker_code'] = ErrorList([ErrorMsg.INVALID_CODE])
      return cfp_render_to_response(request,
        'simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    if speaker.contact_email != form.cleaned_data['contact_email']:
      form.errors['contact_email'] = ErrorList([ErrorMsg.INVALID_EMAIL])
      return cfp_render_to_response(request,
        'simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
      try:
        recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                    request.POST['recaptcha_response_field'],
                                    settings.RECAPTCHA_PRIVATE_KEY,
                                    request.META['REMOTE_ADDR'])
      except:
        return cfp_render_to_response(request,
          'simple_cfp/cfp_error.html',
          {'title': TITLE,
           'error_message': ErrorMsg.CAPTCHA_SERVER_ERROR,
          })
      if not recaptcha_response.is_valid:
        recaptcha_html = GenerateRecaptchaHTML(request,
                                               recaptcha_response.error_code)
        return cfp_render_to_response(request,
          'simple_cfp/cfp_presentation.html',
          {'title': TITLE,
           'form': form,
           'recaptcha_html': recaptcha_html,
           'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
          })

    request.session[Cookies.CFP_LOGIN] = (request.POST['contact_email'],
                                          request.POST['speaker_code'])
    new_presentation = form.save(commit=False)
    new_presentation.speaker = speaker
    new_presentation.submission_code = GeneratePresentationValidationCode()
    new_presentation = form.save()
    form.save_m2m()

    email_sent = False
    if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
      email_sent = SendConfirmationEmail(new_presentation)

    return cfp_render_to_response(request,
      'simple_cfp/cfp_presentation_submitted.html',
      {'title': TITLE,
       'email_sent': email_sent,
       'presentation': new_presentation,
      })
  else:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_presentation.html',
      {'title': TITLE,
       'form': forms.PresentationForm(),
       'recaptcha_html': GenerateRecaptchaHTML(request),
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })

def Logout(request):
  if Cookies.CFP_LOGIN in request.session:
    del request.session[Cookies.CFP_LOGIN]
  if request.META.get('HTTP_REFERER'):
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
  return HttpResponseRedirect('/simple_cfp/')
