from django.urls import path
from apps.goods.views import HomePageView
urlpatterns = [
    path('category/',HomePageView.as_view()),
]