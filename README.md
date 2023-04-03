# Project Name: Meter Management System

The Meter Management System is a web application that allows users to manage their meter readings for various services such as electricity, gas, water, etc. Users can create an account, add and edit meter readings, view previous readings, and manage their profile.

### Requirements

* Python 3.8 or higher
* Django 3.2 or higher
* Other requirements can be found in requirements.txt file
I
### Installation

1. Clone the repository: git clone `https://github.com/suminv/django-meter.git`
2. Install the dependencies by running `pip install -r requirements.txt`
3. Create a new file .env in the root directory and add the following variables:
`SECRET_KEY: Django secret key`
4. Run the migration: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the development server: `python manage.py runserver`

### Usage

To use the application, users must first create an account by registering with their email address and choosing a password. Once logged in, users can add meter readings, view their profile, and update their profile information.

### Features

* User registration and authentication
* Add and edit meter readings
* View previous readings with the difference in readings
* Profile management
* Contributors

Name: Vlad

### License

This project is licensed under the MIT License - see the LICENSE file for details.



