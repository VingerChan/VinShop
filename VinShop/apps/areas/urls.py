from django.urls import path

from apps.areas.views import AreaListView,SubAreaView

# from apps.areas.views import AreaListVIew
urlpatterns = [
    path('areas/',AreaListView.as_view()),
    path('areas/<pk>/',SubAreaView.as_view()),
]