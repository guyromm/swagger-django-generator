"""
Do not modify this file. It is generated from the Swagger specification.

Routing module.
"""
from django.conf.urls import url
from django.conf import settings
from django.views.static import serve
import {{ module }}.views as views
import os

urlpatterns = [
    {# URLs are traverse in reversed sorted order so that longer ones are evaluated first #}
    {% for relative_url, class_name in entries|dictsort(true)|reverse %}
    url(r"^{{ relative_url }}$", views.{{ class_name }}.as_view(), name="{{ class_name|capitalize_splitter }}"),
    {% endfor %}
]

if settings.DEBUG:
    urlpatterns.extend([
        url(r"^the_specification/$", views.__SWAGGER_SPEC__.as_view()),
        url(r"^ui/$", views.ui_index), # said /api/ui/ index override
        url(r"^ui/(?P<path>.*)$", serve, {"document_root": os.path.join(os.path.dirname(__file__),"ui"),
                                          "show_indexes": False})
    ])
