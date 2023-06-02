from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('runAnalysis', views.runAnalysis),
    path('getImages', views.getImages),
    path('image', views.image, name="image"),
]

