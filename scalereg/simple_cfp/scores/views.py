from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from scalereg.common.utils import services_perm_checker
from scalereg.simple_cfp import models

def get_presentation_score(presentation):
  reviews = models.Review.objects.filter(presentation=presentation)
  count = reviews.count()
  if not count:
    return (0, 0)
  score = float(sum([ r.score for r in reviews ])) / count
  return (score, count)


def process_presentations(presentations):
  presentations = presentations.filter(valid=True).all()
  for p in presentations:
    p.comments = models.Comment.objects.filter(presentation=p).count()
    (p.score, p.count) = get_presentation_score(p)
  return presentations


@login_required
def index(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Presentations Scores Overview'

  presentations = models.Presentation.objects.all()
  presentations = process_presentations(presentations)

  return render_to_response('simple_cfp/scores/scores_index.html',
    {'title': TITLE,
     'presentations': presentations,
    })


@login_required
def AudienceIndex(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'List of Audiences'
  TYPE = 'audience'

  audiences = models.Audience.objects.all()
  audiences = [ (obj.id, obj.name) for obj in audiences ]
  return render_to_response('simple_cfp/scores/scores_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': audiences,
    })


@login_required
def Audience(request, id=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Presentations by Audience'

  try:
    audience = models.Audience.objects.get(id=id)
  except models.Audience.DoesNotExist:
    audience = None
  if not audience:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(audiences=audience)
  presentations = process_presentations(presentations)

  return render_to_response('simple_cfp/scores/scores_list.html',
    {'title': TITLE + ': ' + audience.name,
     'presentations': presentations,
    })


@login_required
def CategoryIndex(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'List of Categories'
  TYPE = 'category'

  categories = models.Category.objects.all()
  categories = [ (obj.id, obj.name) for obj in categories ]
  return render_to_response('simple_cfp/scores/scores_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': categories,
    })


@login_required
def Category(request, id=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Presentations by Category'

  try:
    category = models.Category.objects.get(id=id)
  except models.Category.DoesNotExist:
    category = None
  if not category:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(categories=category)
  presentations = process_presentations(presentations)

  return render_to_response('simple_cfp/scores/scores_list.html',
    {'title': TITLE + ': ' + category.name,
     'presentations': presentations,
    })


@login_required
def SpeakerIndex(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'List of Speakers'
  TYPE = 'speaker'

  speakers = models.Speaker.objects.all()
  speakers = [ (obj.id, '%s %s' % (obj.first_name, obj.last_name))
               for obj in speakers ]
  return render_to_response('simple_cfp/scores/scores_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': speakers,
    })


@login_required
def Speaker(request, id=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Presentations by Speaker'

  try:
    speaker = models.Speaker.objects.get(id=id)
  except models.Speaker.DoesNotExist:
    speaker = None
  if not speaker:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(speaker=speaker)
  presentations = process_presentations(presentations)

  return render_to_response('simple_cfp/scores/scores_list.html',
    {'title': TITLE + ': ' + speaker.first_name + ' ' + speaker.last_name,
     'presentations': presentations,
     'speaker': speaker,
    })


@login_required
def StatusIndex(request):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'List of Status'
  TYPE = 'status'

  status = models.STATUS_CHOICES
  return render_to_response('simple_cfp/scores/scores_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': status,
    })


@login_required
def Status(request, status=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Presentations by Status'

  if status not in [ choice[0] for choice in models.STATUS_CHOICES ]:
    status = None
  if not status:
    return HttpResponseServerError('Unknown status')
  presentations = models.Presentation.objects.filter(status=status)
  presentations = process_presentations(presentations)

  return render_to_response('simple_cfp/scores/scores_index.html',
    {'title': TITLE,
     'presentations': presentations,
    })


@login_required
def ReviewPresentation(request, id=None):
  can_access = services_perm_checker(request.user, request.path)
  if not can_access:
    return HttpResponseRedirect('/accounts/profile/')

  TITLE = 'Review Presentations'

  try:
    presentation = models.Presentation.objects.get(id=id)
  except models.Presentation.DoesNotExist:
    presentation = None
  if presentation and not presentation.valid:
    presentation = None
  if not presentation:
    return HttpResponseServerError('Unknown id')

  comments = models.Comment.objects.filter(presentation=presentation)

  if request.method == 'POST':
    action = request.POST.get('action')
    if action == 'comment':
      comment_data = request.POST.get('comment')
      if comment_data:
        comment = models.Comment()
        comment.presentation = presentation
        comment.name = request.user
        comment.comment = comment_data
        try:
          comment.save()
        except:
          pass
      # Fall through to default GET response
    elif action == 'delete':
      id = request.POST.get('delete')
      if id:
        try:
          comment = models.Comment.objects.get(id=id)
        except models.Comment.DoesNotExist:
          comment = None
        if comment and comment.name == request.user:
          comment.delete()
      # Fall through to default GET response
    else:
      pass # Ignore, fall through to default GET response

  (score, num_reviews) = get_presentation_score(presentation)

  return render_to_response('simple_cfp/scores/scores_presentation.html',
    {'title': TITLE,
     'comments': comments,
     'num_reviews': num_reviews,
     'presentation': presentation,
     'score': score,
    })
