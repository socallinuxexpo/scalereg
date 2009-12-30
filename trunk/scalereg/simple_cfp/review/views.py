from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from scalereg.simple_cfp import models

def separate_unreviewed_presentations(my_reviews, all_presentations):
  reviewed = [ r.presentation for r in my_reviews ]
  unreviewed = [ p for p in all_presentations.all() if p not in reviewed ]
  return (reviewed, unreviewed)


@login_required
def index(request):
  TITLE = 'Review Presentations Overview'

  all = models.Presentation.objects.filter(valid=True)

  approved = all.filter(status='Approved')
  pending = all.filter(status='Pending')
  denied = all.filter(status='Denied')
  cancelled = all.filter(status='Cancelled')
  alternate = all.filter(status='Alternate')

  my_reviews = models.Review.objects.filter(name=request.user)
  (reviewed, unreviewed) = separate_unreviewed_presentations(my_reviews, all)

  return render_to_response('simple_cfp/review/review_index.html',
    {'title': TITLE,
     'all': all,
     'approved': approved,
     'pending': pending,
     'denied': denied,
     'cancelled': cancelled,
     'alternate': alternate,
     'reviewed': reviewed,
     'unreviewed': unreviewed,
    })


@login_required
def AudienceIndex(request):
  TITLE = 'List of Audiences'
  TYPE = 'audience'

  audiences = models.Audience.objects.all()
  audiences = [ (obj.id, obj.name) for obj in audiences ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': audiences,
    })


@login_required
def Audience(request, id=None):
  TITLE = 'Presentations by Audience'

  try:
    audience = models.Audience.objects.get(id=id)
  except models.Audience.DoesNotExist:
    audience = None
  if not audience:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(audiences=audience)
  presentations = presentations.filter(valid=True)

  my_reviews = models.Review.objects.filter(name=request.user)
  my_reviews = [ r for r in my_reviews
                 if audience in r.presentation.audiences.all() ]
  (reviewed, unreviewed) = separate_unreviewed_presentations(my_reviews,
                                                             presentations)

  return render_to_response('simple_cfp/review/review_list.html',
    {'title': TITLE + ': ' + audience.name,
     'reviewed': reviewed,
     'unreviewed': unreviewed,
    })


@login_required
def CategoryIndex(request):
  TITLE = 'List of Categories'
  TYPE = 'category'

  categories = models.Category.objects.all()
  categories = [ (obj.id, obj.name) for obj in categories ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': categories,
    })


@login_required
def Category(request, id=None):
  TITLE = 'Presentations by Category'

  try:
    category = models.Category.objects.get(id=id)
  except models.Category.DoesNotExist:
    category = None
  if not category:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(categories=category)
  presentations = presentations.filter(valid=True)

  my_reviews = models.Review.objects.filter(name=request.user)
  my_reviews = [ r for r in my_reviews
                 if category in r.presentation.categories.all() ]
  (reviewed, unreviewed) = separate_unreviewed_presentations(my_reviews,
                                                             presentations)

  return render_to_response('simple_cfp/review/review_list.html',
    {'title': TITLE + ': ' + category.name,
     'reviewed': reviewed,
     'unreviewed': unreviewed,
    })


@login_required
def SpeakerIndex(request):
  TITLE = 'List of Speakers'
  TYPE = 'speaker'

  speakers = models.Speaker.objects.all()
  speakers = [ (obj.id, '%s %s' % (obj.first_name, obj.last_name))
               for obj in speakers ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': speakers,
    })


@login_required
def Speaker(request, id=None):
  TITLE = 'Presentations by Speaker'

  try:
    speaker = models.Speaker.objects.get(id=id)
  except models.Speaker.DoesNotExist:
    speaker = None
  if not speaker:
    return HttpResponseServerError('Unknown id')
  presentations = models.Presentation.objects.filter(speaker=speaker)
  presentations = presentations.filter(valid=True)

  my_reviews = models.Review.objects.filter(name=request.user)
  my_reviews = [ r for r in my_reviews if r.presentation.speaker == speaker ]
  (reviewed, unreviewed) = separate_unreviewed_presentations(my_reviews,
                                                             presentations)

  return render_to_response('simple_cfp/review/review_list.html',
    {'title': TITLE + ': ' + speaker.first_name + ' ' + speaker.last_name,
     'reviewed': reviewed,
     'unreviewed': unreviewed,
    })


@login_required
def StatusIndex(request):
  TITLE = 'List of Status'
  TYPE = 'status'

  status = models.STATUS_CHOICES
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': status,
    })


@login_required
def Status(request, status=None):
  TITLE = 'Presentations by Speaker'

  if status not in [ choice[0] for choice in models.STATUS_CHOICES ]:
    status = None
  if not status:
    return HttpResponseServerError('Unknown status')
  presentations = models.Presentation.objects.filter(status=status)
  presentations = presentations.filter(valid=True)

  my_reviews = models.Review.objects.filter(name=request.user)
  my_reviews = [ r for r in my_reviews if r.presentation.status == status ]
  (reviewed, unreviewed) = separate_unreviewed_presentations(my_reviews,
                                                             presentations)

  return render_to_response('simple_cfp/review/review_list.html',
    {'title': TITLE + ': ' + status,
     'reviewed': reviewed,
     'unreviewed': unreviewed,
    })


@login_required
def ReviewPresentation(request, id=None):
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

  review = models.Review.objects.filter(presentation=presentation)
  try:
    review = review.get(name=request.user)
  except models.Review.DoesNotExist:
    review = None

  if request.method == 'POST':
    action = request.POST.get('action')
    if action == 'score':
      try:
        score = int(request.POST.get('score'))
      except ValueError:
        score = 0
      if score >= 1 and score <= 5:
        if not review:
          review = models.Review()
          review.presentation = presentation
          review.name = request.user
        review.score = score
        review.save()
      # Fall through to default GET response
    elif action == 'comment':
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

  return render_to_response('simple_cfp/review/review_presentation.html',
    {'title': TITLE,
     'comments': comments,
     'presentation': presentation,
     'review': review,
     'user': request.user,
    })
