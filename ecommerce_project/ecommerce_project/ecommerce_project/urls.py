from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Django's built-in administration site.
    path('admin/', admin.site.urls),

    # Redirects the root URL ('/') to your app's login page.
    path('', RedirectView.as_view(url='ecommerce_app/login/', permanent=True)),

    # Includes all the URL patterns from your ecommerce_app.
    # This single line handles both your web pages AND your API endpoints
    # because they are all defined in ecommerce_app/urls.py.
    path('ecommerce_app/', include('ecommerce_app.urls')),
]
