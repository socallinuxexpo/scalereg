from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import get_resolver
from django.urls.resolvers import URLPattern


@staff_member_required
def sales_dashboard(request, report_name):
    pass


@staff_member_required
def index(request):
    model_list = []
    for pattern in get_resolver('reports.urls').url_patterns:
        if not isinstance(pattern, URLPattern):
            continue
        name = pattern.default_args.get('report_name', None)
        if not name:
            continue
        model_list.append({'name': name, 'url': pattern.pattern})

    return render(request, 'reports_index.html', {
        'user': request.user,
        'title': 'Reports',
        'model_list': model_list
    })
