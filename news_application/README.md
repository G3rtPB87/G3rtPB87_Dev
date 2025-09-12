\# News Application Platform

# This is a Django-based news application that serves as a platform for independent journalists and publishers. It features a robust user management system with distinct roles, a subscription service for readers, and an automated content dissemination system.

\---

\#\# Table of Contents  
\- \[Features\](\#features)  
\- \[Technology Stack\](\#technology-in-use)  
\- \[Installation\](\#installation)  
\- \[Database Setup\](\#database-setup)  
\- \[Configuration\](\#configuration)  
\- \[Usage\](\#usage)  
\- \[API Documentation\](\#api-documentation)  
\- \[Testing\](\#testing)  
\- \[Troubleshooting\](\#troubleshooting)  
\- \[License\](\#license)

\#\#\# Features

* # Custom User Roles: Differentiated roles for Reader, Journalist, and Editor.

* # Content Management: A system for journalists to create and manage articles and newsletters, and for editors to approve them.

* # Subscription Service: Readers can subscribe to their favorite publishers and journalists.

* Publisher Functions: This needs to be created in the admin site directly once you have created the superuser  
* Automated Dissemination: Approved content is automatically sent to subscribers via email and posted to an X (formerly Twitter) account using signals.  
* RESTful API: An API for third-party clients to retrieve content based on subscriptions.

\#\#\# Content Management  
\- Article creation and editing.  
\- Newsletter management.  
\- Content approval workflow.  
\- Automated publishing system.

\#\#\# Subscription Service  
\- Users can subscribe to publishers and journalists.  
\- Personalized content feeds.  
\- Email notifications for new content.

\#\#\# Automated Distribution  
\- Automatic posting to X (Twitter) upon content approval.  
\- Email notifications to subscribers.  
\- Social media integration.

\#\#\# RESTful API  
\- A comprehensive \*\*API\*\* for third-party integrations.  
\- Subscription-based content access.  
\- Role-based API permissions.

\---

\#\# Technology Stack  
\- \*\*Backend\*\*: Django 4.2+, Django REST Framework  
\- \*\*Database\*\*: MariaDB/MySQL  
\- \*\*Frontend\*\*: HTML5, Tailwind CSS, JavaScript  
\- \*\*Authentication\*\*: Django Auth System  
\- \*\*API\*\*: Django REST Framework  
\- \*\*Social Media\*\*: X (Twitter) API integration  
\- \*\*Email\*\*: SMTP integration

\---

\#\# Installation  
\#\#\# Prerequisites  
\- Python 3.8+  
\- MariaDB Server  
\- pip (Python package manager)  
\- Virtualenv (recommended)

\#\#\# Step 1: Clone the Repository  
\`\`\`bash  
git clone \[https://github.com/G3rtPB87/G3rtPB87\_Dev.git\](https://github.com/G3rtPB87/G3rtPB87\_Dev.git)  
cd G3rtPB87\_Dev

### **Step 2: Create a Virtual Environment**

Bash  
\# macOS/Linux  
python3 \-m venv venv  
source venv/bin/activate

\# Windows  
python \-m venv venv  
venv\\Scripts\\activate

### **Step 3: Install Dependencies**

Bash  
pip install \-r requirements.txt

---

## **Database Setup**

### **Step 1: Create a MariaDB Database**

SQL  
CREATE DATABASE news\_application\_db;  
CREATE USER 'news\_user'@'localhost' IDENTIFIED BY 'your\_secure\_password';  
GRANT ALL PRIVILEGES ON news\_application\_db.\* TO 'news\_user'@'localhost';  
FLUSH PRIVILEGES;

### 

### **Step 2: Configure Database Settings**

Update `news_application/settings.py` with the following:

Python  
DATABASES \= {  
    'default': {  
        'ENGINE': 'django.db.backends.mysql',  
        'NAME': 'news\_application\_db',  
        'USER': 'news\_user',  
        'PASSWORD': 'your\_secure\_password',  
        'HOST': 'localhost',  
        'PORT': '3306',  
        'OPTIONS': {  
            'init\_command': "SET sql\_mode='STRICT\_TRANS\_TABLES'",  
        }  
    }  
}

---

## **Configuration**

### **Environment Variables**

These settings needs to be updated inside the settings.py

\# news\_application/settings.py   
DATABASES \= { 'default': { 'ENGINE': '[django.db](http://django.db).backends.mysql',  
 'NAME': 'news\_application\_db',  
 'USER': 'news\_user',  
 'PASSWORD': 'your\_secure\_password',  
 'HOST': 'localhost',  
 'PORT': '3306',  
'OPTIONS': { 'init\_command': "SET sql\_mode='STRICT\_TRANS\_TABLES'",   
}   
}   
}

\# Email Configuration  
EMAIL\_HOST=smtp.gmail.com  
EMAIL\_PORT=587  
EMAIL\_USE\_TLS=True  
EMAIL\_HOST\_USER=your-email@gmail.com  
EMAIL\_HOST\_PASSWORD=your-app-password  
DEFAULT\_FROM\_EMAIL=[your-email@gmail.com](mailto:your-email@gmail.com)

For X Integration, you need to update the [signals.py](http://signals.py) file

\# X (Twitter) API Configuration  
X\_API\_KEY=your-x-api-key  
X\_API\_SECRET=your-x-api-secret  
X\_ACCESS\_TOKEN=your-x-access-token  
X\_ACCESS\_SECRET=your-x-access-secret

### **Initial Setup Commands**

Bash  
\# Run migrations  
python manage.py makemigrations  
python manage.py migrate

\# Create a superuser  
python manage.py createsuperuser

\# Collect static files  
python manage.py collectstatic

\# Start the development server  
python manage.py runserver

---

## **Usage**

### **Access Points**

* **Home Page**: `http://localhost:8000/` \- Public content  
* **Reader Dashboard**: `http://localhost:8000/dashboard/` \- Personalized feed  
* **Journalist Dashboard**: `http://localhost:8000/journalist/dashboard/`  
* **Editor Dashboard**: `http://localhost:8000/editor/dashboard/`  
* **Admin Panel**: `http://localhost:8000/admin/`

### **User Roles Workflow**

* **For Readers**:  
  * Register/login with the reader role.  
  * Browse publishers and journalists on the home page.  
  * Subscribe to preferred content creators.  
  * View personalized content in the dashboard.  
* **For Journalists**:  
  * Register/login with the journalist role.  
  * Create articles and newsletters.  
  * Submit content for editor approval.  
  * Manage existing content.  
* **For Editors**:  
  * Login with the editor role.  
  * Review pending content in the editor dashboard.  
  * Approve or reject submissions.  
  * Manage published content.

---

## 

## 

## 

## **API Documentation**

### **Authentication Required Endpoints**

| Endpoint | Method | Description | Required Role |
| :---- | :---- | :---- | :---- |
| `/api/articles/subscribed/` | `GET` | Get a subscriber's articles | Reader |
| `/api/newsletters/subscribed/` | `GET` | Get a subscriber's newsletters | Reader |
| `/api/articles/approve/<id>/` | `POST` | Approve an article | Editor |
| `/api/newsletters/approve/<id>/` | `POST` | Approve a newsletter | Editor |

Export to Sheets

### **Example API Usage**

JavaScript  
// Get subscribed articles  
fetch('/api/articles/subscribed/', {  
    headers: {  
        'Content-Type': 'application/json',  
    },  
    credentials: 'include'  
}).then(response \=\> response.json())  
  .then(data \=\> console.log(data));

---

## **Testing**

### **Run the Complete Test Suite**

Bash  
python manage.py test news

### **Run Specific Test Modules**

Bash  
\# Test models  
python manage.py test news.tests.test\_models

\# Test views  
python manage.py test news.tests.test\_views

\# Test API endpoints  
python manage.py test news.tests.test\_api

\# Test authentication  
python manage.py test news.tests.test\_auth

### 

### **Test Coverage Report**

Bash  
pip install coverage  
coverage run manage.py test news  
coverage report  
coverage html

---

## **Troubleshooting**

### **Common Issues**

**Database Connection Errors**:  
Bash  
\# Ensure MariaDB is running  
sudo systemctl start mariadb

\# Check database user privileges  
mysql \-u root \-p \-e "SHOW GRANTS FOR 'news\_user'@'localhost';"

* 

**Migration Issues**:  
Bash  
\# Reset migrations if needed  
python manage.py makemigrations \--reset  
python manage.py migrate \--fake-initial

* 

**Static Files Not Loading**:  
Bash  
python manage.py collectstatic \--noinput

*   
* **X API Posting Failures**:  
  * Verify API credentials in `.env`.  
  * Check your internet connection.  
  * Verify X API app permissions.  
* **Email Configuration**:  
  * Use app passwords for Gmail.  
  * Enable less secure apps if using other providers.  
  * Check email port settings.

### **Getting Help**

* Check Django error logs in the terminal.  
* Verify all environment variables are set correctly.  
* Ensure all dependencies are installed.  
* Check your database connection settings.  
* Create an issue on the GitHub repository.

---

## **License**

This project is licensed under the **Unlicense License** \- see the `LICENSE` file for details.

---

## **Support**

For support and questions:

* Check the [Django documentation](https://www.google.com/search?q=https://docs.djangoproject.com/en/stable/).  
* Review error messages in the terminal.  
* Create an issue on the GitHub repository.

