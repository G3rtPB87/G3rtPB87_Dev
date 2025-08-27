"""Define models for the e-commerce application.

    Returns:
        _type_: _models for Store, Product, Review, and ResetToken.
"""
from django.db import models
from django.conf import settings


# The Store model represents a vendor's online store.
# Each store is linked to a specific user (vendor) via a foreign key.
class Store(models.Model):
    """
    Represents an online store, owned by a specific user (vendor).
    """
    # Links the store to the User model, representing the vendor.
    # on_delete=models.CASCADE ensures that if a user is deleted,
    # their stores are also deleted.
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        """String for representing the Model object."""
        return self.name


# The Product model represents a product available in a specific store.
# It is linked to the Store model via a foreign key.
class Product(models.Model):
    """
    Represents a product for sale in a store.
    """
    # Links the product to a specific store.
    # on_delete=models.CASCADE ensures that if a store is deleted,
    # its products are also deleted.
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        """String for representing the Model object."""
        return self.name


# The Review model holds reviews left by users for a specific product.
# It includes a flag to determine if the review is verified.
class Review(models.Model):
    """
    Represents a product review.
    """
    # Links the review to a specific product.
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # Links the review to the user who wrote it.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    # A boolean flag to indicate if the review is verified (i.e.,
    # the user purchased the product).
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String for representing the Model object."""
        return f"Review for {self.product.name} by {self.user.username}"


# The ResetToken model is used for the forgotten password feature.
# It tracks a one-time-use token linked to a specific user with an expiry date.
class ResetToken(models.Model):
    """
    Represents a password reset token for a user.
    """
    # Links the token to a specific user.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    # A CharField to store the hashed token value.
    token = models.CharField(max_length=500)
    # The date and time when the token will expire.
    expiry_date = models.DateTimeField()
    # A boolean flag to ensure the token is used only once.
    used = models.BooleanField(default=False)

    def __str__(self):
        """String for representing the Model object."""
        return f"Token for {self.user.username}"
