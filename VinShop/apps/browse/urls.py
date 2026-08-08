from django.urls import path
from apps.browse.views import BrowseHistoryView
urlpatterns = [
    path('browse/',BrowseHistoryView.as_view()),
    path('browse/<sku_id>/',BrowseHistoryView.as_view()),
]