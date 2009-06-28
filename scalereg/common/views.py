from django import http
from django.template import Context, loader
from sys import exc_info

def handler500(request, template_name='500.html', msg=''):
    if not msg:
      msg = exc_info()[1]
    context_dict = {'error_message': msg,
                    'url': request.path,
                   }
    t = loader.get_template(template_name)
    return http.HttpResponseServerError(t.render(Context(context_dict)))
