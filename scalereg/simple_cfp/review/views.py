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
