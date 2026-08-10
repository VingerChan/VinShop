from django.urls import path
from apps.carts.views import CartView,CartSelectAllView,CartItemSelectView,CartItemView,CartDeleteSelectedView

urlpatterns = [
    path('cart/',CartView.as_view()),
    path('cart/selection/',CartSelectAllView.as_view()),
    path('cart/selection/delete/',CartDeleteSelectedView.as_view()),
    path('cart/selection/<int:sku_id>/',CartItemSelectView.as_view()),
    path('cart/<int:sku_id>/', CartItemView.as_view()),
]