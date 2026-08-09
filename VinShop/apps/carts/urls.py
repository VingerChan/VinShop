from django.urls import path
from apps.carts.views import CartView
urlpatterns = [
    path('cart/',CartView.as_view()),
]