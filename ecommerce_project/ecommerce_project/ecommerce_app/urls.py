from django.urls import path
from . import views
from . import api_views  # Import the API views

# URL patterns for the regular web app pages
urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path(
        'send_password_reset/',
        views.send_password_reset,
        name='send_password_reset'
    ),
    path(
        'reset_password/<str:token>/',
        views.reset_user_password,
        name='password_reset'
    ),
    path('create_store/', views.create_store, name='create_store'),
    path('my_stores/', views.list_stores, name='list_stores'),
    path(
        'manage_products/<int:store_id>/',
        views.manage_products,
        name='manage_products'
    ),
    path('products/', views.product_list, name='product_list'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path(
        'submit_review/<int:product_id>/',
        views.submit_review,
        name='submit_review'
    ),
    path(
        'edit_store/<int:store_id>/',
        views.edit_store,
        name='edit_store'
    ),
    path(
        'delete_store/<int:store_id>/',
        views.delete_store,
        name='delete_store'
    ),
    path(
        'edit_product/<int:product_id>/',
        views.edit_product,
        name='edit_product'
    ),
    path(
        'delete_product/<int:product_id>/',
        views.delete_product,
        name='delete_product'
    ),
    path('error_page/', views.error_page, name='error_page'),
]

# URL patterns for the API endpoints
api_urlpatterns = [
    path('api/stores/create/', api_views.add_store_api, name='api_add_store'),
    path(
        'api/products/add/',
        api_views.add_product_api,
        name='api_add_product'
    ),
    path(
        'api/reviews/vendor/',
        api_views.get_reviews_api,
        name='api_get_reviews'
    ),
    path(
        'api/stores/all/',
        api_views.get_public_stores,
        name='api_get_all_stores'
    ),
    path(
        'api/products/all/',
        api_views.get_public_products,
        name='api_get_all_products'
    ),
    path(
        'api/stores/vendor/',
        api_views.get_vendor_stores,
        name='api_get_vendor_stores'
    ),
    path(
        'api/products/vendor/xml/',
        api_views.get_vendor_products_xml,
        name='api_get_vendor_products_xml'
    ),
]

urlpatterns += api_urlpatterns
