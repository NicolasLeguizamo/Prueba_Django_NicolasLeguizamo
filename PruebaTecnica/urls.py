from django.urls import path

from .views import cronograma_view


urlpatterns = [
    path("", cronograma_view, name="cronograma"),
]

