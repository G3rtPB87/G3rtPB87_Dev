# News Application

# This is a Django-based news application that serves as a platform for independent journalists and publishers. It features a robust user management system with distinct roles, a subscription service for readers, and an automated content dissemination system.

# Project Overview

# The application is built with Django and Django REST Framework. It includes:

# 

* # **Custom User Roles:** Differentiated roles for Reader, Journalist, and Editor.

* # **Content Management:** A system for journalists to create and manage articles and newsletters, and for editors to approve them.

* # **Subscription Service:** Readers can subscribe to their favorite publishers and journalists.

* # **Automated Dissemination:** Approved content is automatically sent to subscribers via email and posted to an X (formerly Twitter) account using signals.

* # **RESTful API:** An API for third-party clients to retrieve content based on subscriptions.

# Prerequisites

# You need Python 3.13 and a MariaDB server installed.

# Installation

1. # **Clone the repository:**git clone https://github.com/G3rtPB87/G3rtPB87\_Dev.git

   # 

   # cd ecommerce\_project

   # 

2. # **Create and activate a virtual environment:**

   * # **macOS/Linux:**python3 \-m venv venv

     # 

     # source venv/bin/activate

     # 

   * # **Windows:**python \-m venv venv

     # 

     # venv\\Scripts\\activate

   # 

3. # **Install project dependencies:**pip install \-r requirements.txt

   # 

   # *To create the `requirements.txt` file, run `pip freeze > requirements.txt` before sharing the project.*

# Database Setup

## Configure MariaDB:

1. # Create a database named `news_application_db`.

2. # Create a user named `myuser` with a strong password.

3. # Grant all privileges to `myuser` on the `news_application_db`.

## Update `settings.py`:

# Open `news_application/settings.py`. Update the `DATABASES` dictionary with your MariaDB credentials. Your settings file should also be configured with your X API credentials and email settings.

# Run Migrations

1. # Run the migrations:python manage.py makemigrations news

   # 

   # python manage.py migrate

# Create a Superuser

1. # Create a superuser:python manage.py createsuperuser

# Running the Application

# To run the development server:python manage.py runserver

# How to Test

## Unit Tests

# Run the full test suite to ensure all components, including the API and signal handlers, are working correctly.python manage.py test news

