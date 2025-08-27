from rest_framework import serializers
from .models import Store, Product, Review

class StoreSerializer(serializers.ModelSerializer):
    """
    Serializer for the Store model.
    Converts Store model instances to JSON and validates input data.
    """
    class Meta:
        model = Store
        fields = ['vendor', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    Converts Product model instances to JSON and validates input data.
    """
    class Meta:
        model = Product
        fields = ['store', 'name', 'description', 'price']

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.
    Converts Review model instances to JSON and validates input data.
    """
    class Meta:
        model = Review
        fields = ['product', 'user', 'text', 'is_verified']
