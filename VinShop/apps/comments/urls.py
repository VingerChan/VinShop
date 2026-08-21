from django.urls import path
from apps.comments.views import CommentUploadView,CommentCreateView,CommentListView

urlpatterns = [
    path('comments/upload/',CommentUploadView.as_view()),
    path('comments/',CommentCreateView.as_view()),
    path('goods/<int:sku_id>/comments/',CommentListView.as_view()),
]