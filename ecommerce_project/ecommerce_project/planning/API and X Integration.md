

**1\. API Design: Serialization and Endpoints**

The application's API is built on **RESTful architecture** principles, utilizing standard HTTP methods (GET, POST) and clear URLs to interact with data resources such as stores, products, and reviews.**Serialization**

Serialization is the process of converting complex data types (e.g., Django model instances) into native Python data types, which can then be easily rendered into JSON or other formats.

* **Models**: Serializers have been defined for the Store, Product, and Review models.  
* **Format**: The API primarily uses **JSON** as its data format due to its lightweight nature and widespread adoption in modern web applications.

**Endpoints**

The following endpoints, defined in `ecommerce_app/urls.py`, are routed to their corresponding views in `ecommerce_app/api_views.py`:

* **POST /api/stores/create/:** Allows an authenticated vendor to create a new store.  
* **POST /api/products/add/:** Allows an authenticated vendor to add a new product to their store.  
* **GET /api/reviews/vendor/:** Allows an authenticated vendor to retrieve a list of all reviews for their products.  
* **GET /api/stores/all/:** Provides public access to a list of all stores.  
* **GET /api/products/all/:** Provides public access to a list of all products.  
* **GET /api/stores/vendor/:** Allows an authenticated vendor to retrieve only their own stores.

These can be found in the postman collection **eCommerce-APIs.json**

These endpoints ensure programmatic access to the application's functionality while maintaining appropriate access control for different user roles.  
---

### **2\. X Integration: The `Tweet` Class and Authentication Flow**

The application integrates with the **X API** to automatically post notifications about new stores and products. This is handled by a custom `Tweet` class and a secure authentication process.

#### **The `Tweet` Class**

The `Tweet` class is implemented using the **Singleton pattern**, which ensures that only one instance of the class can exist throughout the application's runtime. This is important because the authentication process with X is time-consuming and should only be performed once. The single instance is accessible via `Tweet._instance`.

#### **Authentication Flow**

The authentication process with the X API uses **OAuth 1.0a** with a PIN-based flow. This is triggered when the Django application first starts up.

1. When the `apps.py` `ready()` method runs, it creates the `Tweet` singleton instance.  
2. The `authenticate` method is called, which initiates the OAuth flow.  
3. The application requests a temporary token and provides a URL for user authorization.  
4. The user visits this URL, logs into their X account, and authorizes the app.  
5. X provides a unique PIN, which the user then pastes into the terminal.  
6. The application uses this PIN to obtain a permanent access token and secret, which are then used for all future API requests.

Once authenticated, the `Tweet` class's `make_tweet` method can be called from within the `create_store` and `manage_products` views to automatically post updates.**2\. X Integration: The Tweet Class and Authentication Flow**

The application integrates with the **X API** to automate notifications regarding new store and product announcements. This functionality is managed through a custom Tweet class and a secure authentication process.**The Tweet Class**

The Tweet class is implemented using the **Singleton pattern**, ensuring that only a single instance of the class exists throughout the application's runtime. This design choice is crucial due to the time-intensive nature of the X authentication process, which should ideally be performed only once. The sole instance is accessible via `Tweet._instance`.**Authentication Flow**

The authentication process with the X API utilizes **OAuth 1.0a** with a PIN-based flow, initiated upon the Django application's initial startup.

1. During the execution of the `apps.py ready()` method, the Tweet singleton instance is created.  
2. The `authenticate` method is invoked, commencing the OAuth flow.  
3. The application requests a temporary token and provides a URL for user authorization.  
4. The user navigates to this URL, logs into their X account, and grants authorization to the application.  
5. X issues a unique PIN, which the user subsequently enters into the terminal.  
6. The application employs this PIN to obtain a permanent access token and secret, which are then used for all subsequent API requests.

Once authenticated, the `Tweet` class's `make_tweet` method can be invoked from within the `create_store` and `manage_products` views to automatically post updates.

