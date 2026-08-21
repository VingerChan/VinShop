from django.urls import path
from apps.comments.views import CommentUploadView,CommentCreateView
urlpatterns = [
    path('comments/upload/',CommentUploadView.as_view()),
    path('comments/',CommentCreateView.as_view()),
]