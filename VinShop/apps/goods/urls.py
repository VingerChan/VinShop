from django.urls import path
from apps.goods.views import HomePageView,RecommendView,SKUDetailView,SearchView
urlpatterns = [
    path('category/',HomePageView.as_view()),
    path('goods/recommend/',RecommendView.as_view()),
    path('goods/<int:sku_id>/',SKUDetailView.as_view()),
    path('search/',SearchView.as_view()),
]