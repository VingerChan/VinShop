from django.urls import path
from apps.carts.views import CartView,CartSelectAllView
urlpatterns = [
    path('cart/',CartView.as_view()),
    path('cart/selection/',CartSelectAllView.as_view()),
]