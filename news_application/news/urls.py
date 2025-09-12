from django.urls import path
from .views import (
    SubscribedArticlesView, ArticleApprovalView, home, register, login_view,
    logout_view, article_detail, dashboard, subscribe, create_article,
    editor_dashboard, journalist_dashboard, create_newsletter,
    NewsletterApprovalView, editor_content_management, SubscribedNewslettersView,
    edit_article, delete_article, edit_newsletter, delete_newsletter
)

urlpatterns = [
    # Main home page
    path('', home, name='home'),

    # User authentication
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # User dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # API endpoints
    path('api/articles/subscribed/', SubscribedArticlesView.as_view(), name='subscribed_articles'),
    path('api/articles/approve/<int:article_id>/', ArticleApprovalView.as_view(), name='article_approval'),
    path('api/newsletters/approve/<int:newsletter_id>/', NewsletterApprovalView.as_view(), name='newsletter_approval'),
    path('api/newsletters/subscribed/', SubscribedNewslettersView.as_view(), name='subscribed_newsletters'),

    # Article details
    path('article/<int:article_id>/', article_detail, name='article_detail'),

    # Subscription functionality
    path('subscribe/<str:subscription_type>/<int:pk>/', subscribe, name='subscribe'),

    # Journalist functions
    path('articles/create/', create_article, name='create_article'),
    path('journalist/dashboard/', journalist_dashboard, name='journalist_dashboard'),
    path('newsletters/create/', create_newsletter, name='create_newsletter'),

    # New URLs for editing and deleting content
    path('articles/edit/<int:pk>/', edit_article, name='edit_article'),
    path('articles/delete/<int:pk>/', delete_article, name='delete_article'),
    path('newsletters/edit/<int:pk>/', edit_newsletter, name='edit_newsletter'),
    path('newsletters/delete/<int:pk>/', delete_newsletter, name='delete_newsletter'),

    # Editor functions
    path('editor/dashboard/', editor_dashboard, name='editor_dashboard'),
    path('editor/content-management/', editor_content_management, name='editor_content_management'),
]