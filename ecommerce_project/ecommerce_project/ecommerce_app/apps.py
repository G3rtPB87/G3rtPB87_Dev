"""Tweet and other functions for the ecommerce app.
"""
from django.apps import AppConfig
from .functions.tweet import Tweet  # Import the Tweet class


class EcommerceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecommerce_app'

    def ready(self):
        """
        Initializes the Tweet class when the app is ready.
        This triggers the authentication process with the X API.
        """
        # Create a single instance of the Tweet class.
        Tweet()
