from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes
from rest_framework.decorators import permission_classes
from rest_framework.decorators import renderer_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_xml.renderers import XMLRenderer
from rest_framework.response import Response
from .models import Store, Product, Review
from .serializers import StoreSerializer, ProductSerializer, ReviewSerializer
from django.contrib.auth.models import User


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_store_api(request):
    """
    API endpoint for vendors to create a new store.
    """
    if request.method == 'POST':
        # Retrieve the authenticated user's ID
        authenticated_user_id = request.user.id

        # Get the vendor username from the request data
        vendor_username = request.data.get('vendor_username')

        try:
            # Find the User ID associated with the provided username
            vendor_user = User.objects.get(username=vendor_username)
            vendor_id_from_payload = vendor_user.id
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'Vendor username not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the authenticated user's ID matches the
        # vendor ID from the payload
        if authenticated_user_id == vendor_id_from_payload:
            # Create a mutable copy of the request data to add the vendor ID
            mutable_data = request.data.copy()
            mutable_data['vendor'] = authenticated_user_id

            serializer = StoreSerializer(data=mutable_data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return JsonResponse(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        return JsonResponse(
            {'ID mismatch': 'User ID and vendor username do not match.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_product_api(request):
    """
    API endpoint for vendors to add a new product to their store.
    """
    if request.method == 'POST':
        # Ensure the store belongs to the authenticated user
        store_id = request.data.get('store')
        if Store.objects.filter(pk=store_id, vendor=request.user).exists():
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return JsonResponse(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return JsonResponse(
            {
                'error': (
                    'You do not have permission to add a product to '
                    'this store.'
                )
            },
            status=status.HTTP_403_FORBIDDEN
        )


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_reviews_api(request):
    """
    API endpoint for vendors to retrieve reviews for all their products.
    """
    if request.method == 'GET':
        # Get all products for the authenticated vendor
        products = Product.objects.filter(store__vendor=request.user)
        # Get all reviews for those products
        reviews = Review.objects.filter(product__in=products)
        serializer = ReviewSerializer(reviews, many=True)
        return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def get_public_stores(request):
    """
    API endpoint to retrieve all stores.
    """
    stores = Store.objects.all()
    serializer = StoreSerializer(stores, many=True)
    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def get_public_products(request):
    """
    API endpoint to retrieve all products.
    """
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_vendor_stores(request):
    """
    API endpoint for vendors to retrieve a list of their stores.
    """
    stores = Store.objects.filter(vendor=request.user)
    serializer = StoreSerializer(stores, many=True)
    return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
@renderer_classes([XMLRenderer])
def get_vendor_products_xml(request):
    """
    API endpoint for vendors to retrieve a list of their products
    in XML format.
    """
    products = Product.objects.filter(store__vendor=request.user)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)
