from django.forms import ModelForm
from scalereg.speaker_survey.models import Survey7X

class Survey7XForm(ModelForm):
  class Meta:
    model = Survey7X
    fields = (
      'q00',
      'q01',
      'q02',
      'q03',
      'q04',
      'q05',
      'q06',
      'q07',
      'q08',
      'q09',
      'q10',
      'q11',
      'q12',
      'q13',
      'q14',
      'comments',
    )
