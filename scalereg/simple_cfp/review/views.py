from django.contrib.auth.decorators import login_required
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
  audiences = [ obj.name for obj in audiences ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': audiences,
    })


@login_required
def CategoryIndex(request):
  TITLE = 'List of Categories'
  TYPE = 'category'

  categories = models.Category.objects.all()
  categories = [ obj.name for obj in categories ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': categories,
    })


@login_required
def SpeakerIndex(request):
  TITLE = 'List of Speakers'
  TYPE = 'speaker'

  speakers = models.Speaker.objects.all()
  speakers = [ '%s %s' % (obj.first_name, obj.last_name) for obj in speakers ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': speakers,
    })


@login_required
def StatusIndex(request):
  TITLE = 'List of Status'
  TYPE = 'status'

  status = [ m[1] for m in models.STATUS_CHOICES ]
  return render_to_response('simple_cfp/review/review_by_type_index.html',
    {'title': TITLE,
     'type': TYPE,
     'list': status,
    })
