from django.urls import path
from apps.goods.views import HomePageView,RecommendView
urlpatterns = [
    path('category/',HomePageView.as_view()),
    path('goods/recommend/',RecommendView.as_view()),
]