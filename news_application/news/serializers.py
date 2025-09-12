from rest_framework import serializers
from .models import Article, Publisher, CustomUser, Newsletter


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model.
    """
    author = serializers.ReadOnlyField(source='author.username')
    publisher = serializers.ReadOnlyField(source='publisher.name')
    published_date = serializers.DateTimeField(
        source='created_at', read_only=True
    )

    # In Django REST framework serializers, the `class Meta`
    # inner class is used to provide metadata
    # about the serializer class. It allows you to define
    # various options and configurations for how
    # the serializer should behave when interacting with Django models.
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'published_date', 'author', 'publisher'
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for the Newsletter model.
    """
    author = serializers.ReadOnlyField(source='author.username')
    publisher = serializers.ReadOnlyField(source='publisher.name')
    published_date = serializers.DateTimeField(
        source='created_at', read_only=True
    )

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'content', 'published_date', 'author', 'publisher'
        ]


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for the Publisher model, including articles and journalists.
    """
    articles = ArticleSerializer(many=True, read_only=True)
    journalists = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'description', 'articles', 'journalists'
        ]


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model, focusing on subscriptions.
    """
    subscriptions_publishers = serializers.StringRelatedField(
        many=True, read_only=True
    )
    subscriptions_journalists = serializers.StringRelatedField(
        many=True, read_only=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'role',
            'subscriptions_publishers', 'subscriptions_journalists'
        ]
