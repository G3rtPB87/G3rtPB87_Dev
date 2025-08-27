# **GB's Online Market**

This is a Django-based eCommerce web application that allows users to register as either buyers or vendors. The application includes core functionality for user management, product management, and a shopping cart system.

## **Features**

### **Authentication & User Management**

* **User Registration & Login**: Users can sign up and log in as either a buyer or a vendor. Duplicate email validation is in place to prevent multiple accounts from using the same email address.  
* **Password Reset**: A secure password reset flow is implemented using an expiring, token-based URL. For development and testing, this sends an email to the console.

### **Vendor Functionality**

* **Store Management**: Vendors can create, view, edit, and delete their own stores. The system prevents a store from being deleted if it contains products.  
* **Product Management**: Vendors can add, view, edit, and delete products within their stores.

### **Buyer Functionality**

* **Product Browsing**: All users can view a list of all products from every store, with the store's name displayed for each product. The currency has been updated to **Rands (R)**.  
* **Shopping Cart**: Buyers can add products to a session-based shopping cart, and a count of items is displayed in the navigation bar.  
* **Checkout**: The checkout process generates an invoice (printed to the console) and clears the cart.  
* **Reviews**: Buyers can leave reviews on any product. The system correctly identifies and labels reviews from buyers as "Verified", while vendors are explicitly prevented from leaving reviews.

### **API Integration**

* **RESTful API**: The application includes a set of RESTful API endpoints for external clients to interact with stores, products, and reviews.  
* **Third-Party API**: The Twitter (X) API is integrated to automatically post a tweet whenever a new store or product is added.

## 

## **Getting Started**

### **Prerequisites**

* **Python 3.x**  
* **pip** (Python package installer)

### **Installation**

1. **Clone the repository:**  
   git clone https://github.com/G3rtPB87/G3rtPB87\_Dev.git  
   cd ecommerce\_project

2. **Create and activate a virtual environment:**  
   * **macOS/Linux:**  
     python3 \-m venv venv  
     source venv/bin/activate

   * **Windows:**  
     python \-m venv venv  
     venv\\Scripts\\activate

3. **Install project dependencies:**  
   pip install \-r requirements.txt

   *To create the requirements.txt file, run pip freeze \> requirements.txt before sharing the project.*

## **Usage**

1. **Run migrations to set up the database:**  
   python3 manage.py migrate

2. **Create a superuser for admin access:**  
   python3 manage.py createsuperuser

3. **Start the development server:**  
   python3 manage.py runserver

4. Open your browser and navigate to http://127.0.0.1:8000/ecommerce\_app/login/.