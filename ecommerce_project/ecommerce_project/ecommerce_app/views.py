from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage
from django.conf import settings
from .models import ResetToken, Store, Product, Review
import secrets
from datetime import datetime, timedelta
from hashlib import sha1
import json
from .functions.tweet import Tweet  # Import the Tweet class


def get_cart_item_count(request):
    """
    Helper function to get the total number of items in the cart.
    """
    cart = request.session.get('cart', {})
    return sum(item['quantity'] for item in cart.values())


# A welcome view that requires a user to be logged in.
# It uses the @login_required decorator to redirect unauthenticated users
# to the login page defined in settings.LOGIN_URL.
@login_required(login_url='/login/')
def welcome(request):
    """
    Renders the welcome page for authenticated users.
    """
    cart_item_count = get_cart_item_count(request)
    return render(
        request,
        'welcome.html',
        {'cart_item_count': cart_item_count}
    )


def register_user(request):
    """
    Handles user registration.
    This view creates a new user and assigns them to a group
    (Buyers by default).
    """
    cart_item_count = get_cart_item_count(request)
    if request.method == 'POST':
        # Get user input from the registration form.
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        account_type = request.POST.get('account_type', 'Buyers')

        # Check if the username already exists.
        if User.objects.filter(username=username).exists():
            return render(
                request,
                'register.html',
                {
                    'error': 'Username already exists.',
                    'cart_item_count': cart_item_count
                }
            )

        # Check if the email already exists.
        if User.objects.filter(email=email).exists():
            return render(
                request,
                'register.html',
                {
                    'error': 'Email already in use.',
                    'cart_item_count': cart_item_count
                }
            )

        try:
            # Create the user object.
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Get the appropriate group and add the user to it.
            # We use get_or_create to ensure the group exists.
            user_group, created = Group.objects.get_or_create(
                name=account_type
            )
            user.groups.add(user_group)

            # Log the user in immediately after registration.
            login(request, user)

            # Redirect to a success page or the welcome page.
            return redirect('welcome')

        except Exception as e:
            # Handle potential errors during user creation or group assignment.
            return render(
                request,
                'register.html',
                {
                    'error': f'An error occurred: {e}',
                    'cart_item_count': cart_item_count
                }
            )

    # If it's a GET request, render the registration form.
    return render(
        request,
        'register.html',
        {'cart_item_count': cart_item_count}
    )


def login_user(request):
    """
    Handles user login.
    It authenticates user credentials and logs them in if they are valid.
    """
    cart_item_count = get_cart_item_count(request)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user. This function returns the
        # User object if successful, or None otherwise.
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in.
            login(request, user)
            return redirect('welcome')
        else:
            # If authentication fails, render the login page
            # with an error message.
            return render(
                request,
                'login.html',
                {
                    'error': 'Invalid username or password.',
                    'cart_item_count': cart_item_count
                }
            )

    # If it's a GET request, render the login form.
    return render(request, 'login.html', {'cart_item_count': cart_item_count})


def logout_user(request):
    """
    Handles user logout.
    It logs the user out and clears the session data.
    """
    if request.user.is_authenticated:
        logout(request)
    # Redirect to the login page after logging out.
    return redirect('login')


def send_password_reset(request):
    """
    Handles the password reset request by sending a reset link to the user's
    email.
    """
    cart_item_count = get_cart_item_count(request)
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            # Find the user by their email address.
            user = User.objects.get(email=email)

            # Generate a secure, URL-safe token.
            token = secrets.token_urlsafe(16)

            # Hash the token before storing it in the database for security.
            hashed_token = sha1(token.encode()).hexdigest()

            # Set a 5-minute expiry date for the token.
            expiry_date = datetime.now() + timedelta(minutes=5)

            # Delete any old tokens for this user to
            # prevent multiple valid tokens.
            ResetToken.objects.filter(user=user).delete()

            # Create and save the new reset token in the database.
            ResetToken.objects.create(
                user=user,
                token=hashed_token,
                expiry_date=expiry_date
            )

            # Build the password reset URL.
            # We assume a URL pattern like: path('reset_password/<str:token>/',
            # reset_user_password, name='password_reset').
            reset_url = request.build_absolute_uri(
                reverse('password_reset', kwargs={'token': token})
            )

            # Prepare and send the email.
            subject = "Password Reset Request"
            body = (
                f"Hello {user.username},\n\n"
                f"Here is your link to reset your password: {reset_url}\n\n"
                "This link will expire in 5 minutes."
            )

            email_message = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.send()

            return render(
                request,
                'send_password_reset_request.html',
                {
                    'success_message': (
                        'A password reset link has been sent to your email.'
                    ),
                    'cart_item_count': cart_item_count
                }
            )

        except User.DoesNotExist:
            # Return a success message even if the user doesn't exist to avoid
            # revealing whether an email address is registered.
            return render(
                request,
                'send_password_reset_request.html',
                {
                    'success_message': (
                        'If a matching account was found, '
                        'a password reset link has been sent.'
                    ),
                    'cart_item_count': cart_item_count
                }
            )

    return render(
        request,
        'send_password_reset_request.html',
        {'cart_item_count': cart_item_count}
    )


def reset_user_password(request, token):
    """
    Handles the password reset link validation and password update.
    """
    cart_item_count = get_cart_item_count(request)
    # Hash the token from the URL to match the one in the database.
    hashed_token = sha1(token.encode()).hexdigest()

    try:
        user_token = ResetToken.objects.get(token=hashed_token, used=False)

        # Check if the token has expired.
        if (
            user_token.expiry_date.replace(tzinfo=None)
            < datetime.now().replace(tzinfo=None)
        ):
            user_token.delete()
            return render(
                request,
                'password_reset.html',
                {
                    'error': 'The password reset link has expired.',
                    'cart_item_count': cart_item_count
                }
            )

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password and new_password == confirm_password:
                # Get the user and set the new password.
                user = user_token.user
                user.set_password(new_password)
                user.save()

                # Mark the token as used to prevent it from being used again.
                user_token.used = True
                user_token.save()

                return render(
                    request,
                    'login.html',
                    {
                        'success_message': (
                            'Your password has been reset successfully. '
                            'Please log in.'
                        ),
                        'cart_item_count': cart_item_count
                    }
                )
            else:
                return render(
                    request,
                    'password_reset.html',
                    {
                        'token': token,
                        'error': 'Passwords do not match.',
                        'cart_item_count': cart_item_count
                    }
                )

        # If it's a GET request, render the password reset form.
        return render(
            request,
            'password_reset.html',
            {
                'token': token,
                'cart_item_count': cart_item_count
            }
        )

    except ResetToken.DoesNotExist:
        return render(
            request,
            'password_reset.html',
            {
                'error': 'Invalid password reset link.',
                'cart_item_count': cart_item_count
            }
        )


@login_required(login_url='/login/')
def create_store(request):
    """
    Allows a logged-in user to create a new store.
    """
    cart_item_count = get_cart_item_count(request)
    # Check if the user is a Vendor.
    if not request.user.groups.filter(name='Vendors').exists():
        # Redirect to a different page or show an error if not a vendor.
        return redirect('welcome')

    if request.method == 'POST':
        # Get the store details from the form.
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Create a new Store object and save it to the database.
        new_store = Store.objects.create(
            vendor=request.user,
            name=name,
            description=description
        )
        new_store.save()

        # Create the tweet text and send the tweet.
        store_tweet_text = (
            f"New store opened on GB's Online Market!\n"
            f"Store: {new_store.name}\n"
            f"Description: {new_store.description}"
        )
        Tweet._instance.make_tweet(store_tweet_text)

        # Redirect to the welcome page or a success page.
        return redirect('welcome')

    # If it's a GET request, render the form to create a store.
    return render(
        request,
        'create_store.html',
        {'cart_item_count': cart_item_count}
    )


@login_required(login_url='/login/')
def list_stores(request):
    """
    Displays a list of all stores for the currently logged-in vendor.
    """
    cart_item_count = get_cart_item_count(request)
    # Check if the user is a Vendor.
    if not request.user.groups.filter(name='Vendors').exists():
        # Redirect to a different page or show an error if not a vendor.
        return redirect('welcome')

    # Get all stores owned by the current user.
    stores = Store.objects.filter(vendor=request.user)

    # Pass the list of stores to the template.
    return render(
        request,
        'list_stores.html',
        {
            'stores': stores,
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def manage_products(request, store_id):
    """
    Allows a vendor to manage products for a specific store.
    """
    cart_item_count = get_cart_item_count(request)
    # Get the store object or return a 404 if it doesn't exist.
    store = get_object_or_404(Store, pk=store_id)

    # Check if the logged-in user is the owner of the store.
    if store.vendor != request.user:
        return redirect('list_stores')  # Redirect if not the owner

    # Handle form submission to create a new product.
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        # Create the new Product object and save it to the database.
        new_product = Product.objects.create(
            store=store,
            name=name,
            description=description,
            price=price
        )
        new_product.save()

        # Create the tweet text and send the tweet.
        product_tweet_text = (
            f"New product added to {store.name} on GB's Online Market!\n"
            f"Product: {new_product.name}\n"
            f"Description: {new_product.description}\n"
            f"Price: R{new_product.price}"
        )
        Tweet._instance.make_tweet(product_tweet_text)

    # Get all products for the current store to display them.
    products = Product.objects.filter(store=store)

    # Pass the store and its products to the template.
    return render(
        request,
        'manage_products.html',
        {
            'store': store,
            'products': products,
            'cart_item_count': cart_item_count
        }
    )


def product_list(request):
    """
    Displays a list of all products from all stores.
    """
    cart_item_count = get_cart_item_count(request)
    products = Product.objects.all()
    return render(
        request,
        'product_list.html',
        {
            'products': products,
            'cart_item_count': cart_item_count
        }
    )


def add_to_cart(request):
    """
    Handles adding products to the user's shopping cart using sessions.
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 1)  # Default quantity is 1

        # Retrieve the product or return a 404.
        product = get_object_or_404(Product, pk=product_id)

        # Get the session cart, or create an empty dictionary if it does not
        # exist.
        cart = request.session.get('cart', {})

        # Add the product to the cart. We store the product ID as the key.
        # We need to store quantity as an integer.
        cart_item = cart.get(str(product_id))
        if cart_item:
            cart_item['quantity'] += int(quantity)
        else:
            cart[str(product_id)] = {
                'id': product.id,
                'quantity': int(quantity)
            }

        # Save the updated cart back to the session.
        request.session['cart'] = cart

        # Redirect back to the product list page after adding to cart.
        return redirect('product_list')

    # If it's not a POST request, redirect to the product list.
    return redirect('product_list')


def view_cart(request):
    """
    Retrieves and displays the contents of the user's shopping cart
    from the session.
    """
    cart_item_count = get_cart_item_count(request)
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = get_object_or_404(Product, pk=item_data['id'])
        quantity = item_data['quantity']
        item_total = product.price * quantity
        total_price += item_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })

    return render(
        request,
        'view_cart.html',
        {
            'cart_items': cart_items,
            'total_price': total_price,
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def checkout(request):
    """
    Handles the checkout process, sends an invoice email, and clears the cart.
    """
    cart_item_count = get_cart_item_count(request)
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    if not cart:
        # Redirect to the cart page if the cart is empty.
        return redirect('view_cart')

    # Get details for each product in the cart.
    for product_id, item_data in cart.items():
        product = get_object_or_404(Product, pk=item_data['id'])
        quantity = item_data['quantity']
        item_total = product.price * quantity
        total_price += item_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })

    # Build the invoice email content.
    email_body = f"Hello {request.user.username},\n\n"
    email_body += "Thank you for your purchase! Here is your invoice:\n\n"
    email_body += "---------------------------------------\n"
    for item in cart_items:
        email_body += f"Product: {item['product'].name}\n"
        email_body += f"Quantity: {item['quantity']}\n"
        email_body += f"Price per item: R{item['product'].price}\n"
        email_body += f"Total: R{item['item_total']}\n"
        email_body += "---------------------------------------\n"
    email_body += f"Grand Total: R{total_price}\n\n"
    email_body += "We hope you enjoy your products!"

    # Create and send the email.
    email_message = EmailMessage(
        subject="Your Invoice",
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.user.email]
    )
    email_message.send()

    # Clear the cart from the session.
    del request.session['cart']

    # Redirect to a confirmation page or the welcome page.
    return redirect('welcome')


def submit_review(request, product_id):
    """
    Handles review submission for a specific product.
    Checks if the user has bought the product to determine if the review is
    verified.
    """
    cart_item_count = get_cart_item_count(request)
    if not request.user.is_authenticated:
        # Redirect to login page if user is not authenticated.
        return redirect('login')

    if request.method == 'POST':
        # Get the product and review text from the form.
        product = get_object_or_404(Product, pk=product_id)
        review_text = request.POST.get('review_text')

        # Check if the user has "purchased" this product.
        # This is a placeholder. A real e-commerce app would
        # check for a completed order.
        # For our purposes, we'll assume a user is "verified"
        # if they are a "Buyer".
        is_verified = False
        if request.user.groups.filter(name='Buyers').exists():
            is_verified = True

        # Create a new Review object and save it to the database.
        Review.objects.create(
            product=product,
            user=request.user,
            text=review_text,
            is_verified=is_verified
        )

        # Redirect back to the product list or a specific product page.
        return redirect('product_list')

    # Redirect to product list if not a POST request.
    return render(
        request,
        'product_list.html',
        {
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def edit_store(request, store_id):
    """
    Allows a vendor to edit their store details.
    """
    cart_item_count = get_cart_item_count(request)
    # Get the store object, ensuring it belongs to the logged-in user.
    store = get_object_or_404(Store, pk=store_id, vendor=request.user)

    if request.method == 'POST':
        store.name = request.POST.get('name')
        store.description = request.POST.get('description')
        store.save()
        return redirect('list_stores')

    return render(
        request,
        'edit_store.html',
        {
            'store': store,
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def delete_store(request, store_id):
    """
    Allows a vendor to delete their store.
    """
    cart_item_count = get_cart_item_count(request)
    store = get_object_or_404(Store, pk=store_id, vendor=request.user)

    # Check if the store has any products before allowing deletion
    if store.product_set.exists():
        return render(
            request,
            'error_page.html',
            {
                'error_message': (
                    "Cannot delete a store with existing products."
                ),
                'cart_item_count': cart_item_count
            }
        )

    if request.method == 'POST':
        store.delete()
        return redirect('list_stores')
    return render(
        request,
        'delete_store.html',
        {
            'store': store,
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def edit_product(request, product_id):
    """
    Allows a vendor to edit a product.
    """
    cart_item_count = get_cart_item_count(request)
    product = get_object_or_404(Product, pk=product_id)
    # Check if the product belongs to a store owned by the current user
    if product.store.vendor != request.user:
        return redirect('welcome')

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.save()
        return redirect('manage_products', store_id=product.store.id)

    return render(
        request,
        'edit_product.html',
        {
            'product': product,
            'cart_item_count': cart_item_count
        }
    )


@login_required(login_url='/login/')
def delete_product(request, product_id):
    """
    Allows a vendor to delete a product.
    """
    cart_item_count = get_cart_item_count(request)
    product = get_object_or_404(Product, pk=product_id)
    if product.store.vendor != request.user:
        return redirect('welcome')

    if request.method == 'POST':
        product.delete()
        return redirect('manage_products', store_id=product.store.id)
    return render(
        request,
        'delete_product.html',
        {
            'product': product,
            'cart_item_count': cart_item_count
        }
    )


def error_page(request):
    """
    Renders a generic error page with a custom message.
    """
    cart_item_count = get_cart_item_count(request)
    return render(
        request,
        'error_page.html',
        {'cart_item_count': cart_item_count}
    )
