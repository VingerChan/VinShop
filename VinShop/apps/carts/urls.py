from django.urls import path
from apps.carts.views import CartView,CartSelectAllView,CartItemSelectView

urlpatterns = [
    path('cart/',CartView.as_view()),
    path('cart/selection/',CartSelectAllView.as_view()),
    path('cart/selection/<sku_id>/',CartItemSelectView.as_view()),
]