from django.conf import settings
from django.forms.util import ErrorList
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from scalereg.common import utils
from scalereg.simple_cfp import forms
from scalereg.simple_cfp import models

if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
  from django.core.mail import send_mail
  from django.core.mail import BadHeaderError
  import smtplib

if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
  from recaptcha.client.captcha import displayhtml
  from recaptcha.client.captcha import submit

class ErrorMsg:
  # Common messages
  EMAIL_ERROR = 'Could not send email'
  # SubmitPresentation
  INVALID_ADSP = 'Invalid additional speaker'
  INVALID_CODE = 'Invalid speaker code'
  INVALID_EMAIL = 'Email address does not match speaker code'
  # SubmissionStatus
  DELETE_SUCCESS = 'Presentation successfully deleted'
  DELETE_FAIL = 'Could not delete presentation'
  INVALID_CREDENTIAL = 'Cannot find speaker with given info'
  INVALID_INCOMPLETE = 'Please fill out all the fields'
  UPLOAD_SUCCESS = 'Presentation successfully uploaded'
  UPLOAD_FAIL = 'Could not upload presentation'


class Cookies:
  CFP_LOGIN = 'cfp_login'


class RSSMsg:
  LINK = 'http://www.foobar.com' # CHANGE_THIS
  ORG = 'Foo Bar Corporation' # CHANGE_THIS


def DoRecaptchaValidation(request, template, template_dict):
  if settings.SCALEREG_SIMPLECFP_USE_RECAPTCHA:
    try:
      recaptcha_response = submit(request.POST['recaptcha_challenge_field'],
                                  request.POST['recaptcha_response_field'],
                                  settings.RECAPTCHA_PRIVATE_KEY,
                                  request.META['REMOTE_ADDR'])
    except:
      # If we cannot get a recaptcha, let the user continue.
      return None
    if not recaptcha_response.is_valid:
      template_dict['recaptcha_html'] = GenerateRecaptchaHTML(request,
        recaptcha_response.error_code)
      return cfp_render_to_response(request, template, template_dict)
  return None


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
              '''Your presentation: %s has been submitted for:
%s
Your simple_cfp submission code is %s.''' % \
              (presentation.title, presentation.speaker.email,
               presentation.submission_code),
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
              '''Your simple_cfp validation code for %s is: %s.
If this email was sent to you by mistake, please reply and let us know.''' % \
              (speaker.email, speaker.validation_code),
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
    contact_email = request.POST.get('contact_email')
    email = request.POST.get('email')

    recaptcha_response = DoRecaptchaValidation(request,
      'simple_cfp/cfp_recover_validation.html',
      {'title': TITLE,
       'email': email,
      })
    if recaptcha_response:
      return recaptcha_response

    speakers = models.Speaker.objects.filter(contact_email=contact_email,
      email=email)
    speakers = speakers.filter(valid=True)
    if not speakers:
      return cfp_render_to_response(request,
        'simple_cfp/cfp_recover_validation.html',
        {'title': TITLE,
         'contact_email': contact_email,
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
       'contact_email': contact_email,
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
  TITLE = 'Speaker Registration'

  if request.method == 'POST':
    form = forms.SpeakerForm(request.POST)
    if not form.is_valid():
      return cfp_render_to_response(request,
        'simple_cfp/cfp_speaker.html',
        {'title': TITLE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    recaptcha_response = DoRecaptchaValidation(request,
      'simple_cfp/cfp_speaker.html',
      {'title': TITLE,
       'form': form,
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })
    if recaptcha_response:
      return recaptcha_response

    new_speaker = form.save(commit=False)
    new_speaker.validation_code = GenerateSpeakerValidationCode()
    new_speaker = form.save()

    photo_url = None
    if (settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD and
        'photo_upload' in request.FILES):
      new_photo = models.SpeakerPhoto()
      new_photo.speaker_id = new_speaker.id
      photo_file = request.FILES['photo_upload']
      new_photo.file.save(photo_file.name, photo_file)
      new_photo.save()
      photo_url = new_photo.file.url

    email_sent = False
    if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
      email_sent = SendValidationEmail(new_speaker)

    return cfp_render_to_response(request,
      'simple_cfp/cfp_speaker_registered.html',
      {'title': TITLE,
       'email_sent': email_sent,
       'photo_url': photo_url,
       'speaker': new_speaker,
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })
  else:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_speaker.html',
      {'title': TITLE,
       'form': forms.SpeakerForm(),
       'recaptcha_html': GenerateRecaptchaHTML(request),
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })


def SubmissionStatus(request):
  TITLE = 'Submission Status'

  code = request.REQUEST.get('code')
  contact_email = request.REQUEST.get('contact_email')
  speaker_email = request.REQUEST.get('speaker_email')
  if not (code and contact_email and speaker_email):
    try:
      (code, contact_email, speaker_email) = request.session[Cookies.CFP_LOGIN]
    except:
      pass

  if not (code and contact_email and speaker_email):
    error = ''
    if request.method == 'POST':
      error = ErrorMsg.INVALID_INCOMPLETE
    return cfp_render_to_response(request,
      'simple_cfp/cfp_submission_status.html',
      {'title': TITLE,
       'error': ErrorMsg.INVALID_INCOMPLETE,
       'code': code,
       'contact_email': contact_email,
       'speaker_email': speaker_email,
      })

  speaker = None
  try:
    speaker = models.Speaker.objects.get(validation_code=code,
      contact_email=contact_email, email=speaker_email)
  except models.Speaker.DoesNotExist:
    pass

  if not speaker:
    return cfp_render_to_response(request,
      'simple_cfp/cfp_submission_status.html',
      {'title': TITLE,
       'error': ErrorMsg.INVALID_CREDENTIAL,
       'code': code,
       'contact_email': contact_email,
       'speaker_email': speaker_email,
      })

  presentations = models.Presentation.objects.filter(speaker=speaker)
  request.session[Cookies.CFP_LOGIN] = (code, contact_email, speaker_email)

  # Handle new uploads and deletes
  error = ''
  if settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD and request.method == 'POST':
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
     'contact_email': contact_email,
     'error': error,
     'presentations': presentations,
     'speaker_email': speaker_email,
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

    additional_speakers = set()
    invalid_speakers = set()
    for sp in form.data['additional_speakers'].split(','):
      if not sp:
        continue
      sp = sp.strip()
      try:
        adsp = models.Speaker.objects.get(email=sp)
        additional_speakers.add(adsp)
      except models.Speaker.DoesNotExist:
        invalid_speakers.add(sp)
    if invalid_speakers:
      form.errors['additional_speakers'] = ErrorList([
          ErrorMsg.INVALID_ADSP + ': ' + ', '.join(invalid_speakers)])

    if not form.is_valid() or invalid_speakers:
      return cfp_render_to_response(request,
        'simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'file_limit': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
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
         'file_limit': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    bad_email = False
    if speaker.contact_email != form.cleaned_data['contact_email']:
      form.errors['contact_email'] = ErrorList([ErrorMsg.INVALID_EMAIL])
      bad_email = True
    if speaker.email != form.cleaned_data['speaker_email']:
      form.errors['speaker_email'] = ErrorList([ErrorMsg.INVALID_EMAIL])
      bad_email = True

    if bad_email:
      return cfp_render_to_response(request,
        'simple_cfp/cfp_presentation.html',
        {'title': TITLE,
         'file_limit': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
         'form': form,
         'recaptcha_html': GenerateRecaptchaHTML(request),
         'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
        })

    recaptcha_response = DoRecaptchaValidation(request,
      'simple_cfp/cfp_presentation.html',
      {'title': TITLE,
       'file_limit': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
       'form': form,
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })
    if recaptcha_response:
      return recaptcha_response

    request.session[Cookies.CFP_LOGIN] = (request.POST['speaker_code'],
                                          request.POST['contact_email'],
                                          request.POST['speaker_email'])
    new_presentation = form.save(commit=False)
    new_presentation.speaker = speaker
    new_presentation.submission_code = GeneratePresentationValidationCode()
    new_presentation = form.save()
    form.save_m2m()

    for sp in additional_speakers:
      adsp = models.AdditionalSpeaker()
      adsp.speaker = sp
      adsp.presentation = new_presentation;
      adsp.save()

    email_sent = False
    if settings.SCALEREG_SIMPLECFP_SEND_MAIL:
      email_sent = SendConfirmationEmail(new_presentation)

    return cfp_render_to_response(request,
      'simple_cfp/cfp_presentation_submitted.html',
      {'title': TITLE,
       'additional_speakers': additional_speakers,
       'email_sent': email_sent,
       'presentation': new_presentation,
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })
  else:
    form = forms.PresentationForm()
    try:
      (code, contact_email, speaker_email) = request.session[Cookies.CFP_LOGIN]
      form.fields['speaker_code'].initial = code
      form.fields['contact_email'].initial = contact_email
      form.fields['speaker_email'].initial = speaker_email
    except:
      pass

    return cfp_render_to_response(request,
      'simple_cfp/cfp_presentation.html',
      {'title': TITLE,
       'file_limit': settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
       'form': form,
       'recaptcha_html': GenerateRecaptchaHTML(request),
       'upload': settings.SCALEREG_SIMPLECFP_ALLOW_UPLOAD,
      })

def Logout(request):
  if Cookies.CFP_LOGIN in request.session:
    del request.session[Cookies.CFP_LOGIN]
  if request.META.get('HTTP_REFERER'):
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
  return HttpResponseRedirect('/simple_cfp/')


def AcceptedPresentations(request):
  TITLE = 'Accepted Presentations'
  DESC = 'Accepted Presentations for the '

  presentations = models.Presentation.objects.filter(valid=True)
  presentations = presentations.filter(status='Approved')
  additional_speakers = []
  for p in presentations:
    # easier to preformat this now rather than doing it in the template.
    adsp = models.AdditionalSpeaker.objects.filter(presentation=p)
    adsp_text = ','.join('s%d' % s.speaker.id for s in adsp)
    p.speakers = 's%d' % p.speaker.id
    if adsp_text:
      p.speakers += ',' + adsp_text

  return render_to_response('simple_cfp/rss_presentation.html',
    {'title': TITLE,
     'link': RSSMsg.LINK,
     'additional_speakers': additional_speakers,
     'desc': DESC + RSSMsg.ORG,
     'presentations': presentations,
    })


def AcceptedSpeakers(request):
  TITLE = 'Accepted Speakers'
  DESC = 'Accepted Speakers for the '

  presentations = models.Presentation.objects.filter(valid=True)
  presentations = presentations.filter(status='Approved')
  speakers = [p.speaker for p in presentations]
  speakers = [p.speaker for p in presentations]
  additional_speakers = models.AdditionalSpeaker.objects.all()
  speakers += [adsp.speaker for adsp in additional_speakers if
               adsp.presentation.valid and
               adsp.presentation.status == 'Approved']
  speakers = list(set(speakers))
  for sp in speakers:
    photos = models.SpeakerPhoto.objects.filter(speaker=sp)
    sp.photo_urls = ' '.join([s.file.url for s in photos])

  return render_to_response('simple_cfp/rss_speaker.html',
    {'title': TITLE,
     'link': RSSMsg.LINK,
     'desc': DESC + RSSMsg.ORG,
     'speakers': speakers,
    })
