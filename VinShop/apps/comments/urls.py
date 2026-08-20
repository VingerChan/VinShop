from django.urls import path
from apps.comments.views import CommentUploadView
urlpatterns = [
    path('comments/upload/',CommentUploadView.as_view()),
]