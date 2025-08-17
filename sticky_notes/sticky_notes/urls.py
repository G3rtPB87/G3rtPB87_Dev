from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Admin URL pattern, mapping to the Django admin interface
    path("admin/", admin.site.urls),

    # Include URL patterns from the 'notes' app
    # All URLs from 'notes.urls' will be prefixed with '/'
    path("", include("notes.urls")),
]
