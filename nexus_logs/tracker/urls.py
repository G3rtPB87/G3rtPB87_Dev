from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_timeline, name="upload_timeline"),
    path("entry/<int:pk>/edit/", views.edit_entry, name="edit_entry"),
    path("entry/<int:pk>/delete/", views.delete_entry, name="delete_entry"),
    path("manual-entry/", views.manual_entry, name="manual_entry"),
    path("export/", views.export, name="export"),
    path("config/", views.config_view, name="config"),
]
