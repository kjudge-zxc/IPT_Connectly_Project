# Connectly Project

Connectly is a social media API project developed for our Integrative Programming and Technologies class (S3101). It is built using Django and Django REST Framework.

## Features

- User registration and login
- Role-based access control (Admin, Moderator, User)
- Follow and unfollow users
- Create posts with privacy settings
  - Public
  - Private
  - Friends-only
- View posts based on visibility permissions
- Delete posts with author/admin restrictions
- Update user roles (admin only)
- Personalized news feed
- Feed pagination
- Feed caching and cache management
- Likes and comments

## Tech Stack

- Python
- Django
- Django REST Framework (DRF)
- SQLite
- Postman for API testing

## Project Structure

- `users/` – user management and roles
- `posts/` – posts, feed, likes, comments, and follow system
- `connectly_project/` – main project 

## How to Run the Project

1. Clone the repository  
   `git clone IPT_Connectly_Project`

2. Go to the project folder  
   `cd connectly_project`

3. Create and activate a virtual environment

   **Windows**  
   `python -m venv venv`  
   `venv\Scripts\activate`

   **Mac/Linux**  
   `python3 -m venv venv`  
   `source venv/bin/activate`

4. Install dependencies  
   `pip install -r requirements.txt`

5. Run migrations  
   `python manage.py migrate`

6. Start the development server  
   `python manage.py runserver`

7. Test the API using Postman


## Group 14
Martin Sheen Cajucom & Angelique Gail Macaspac
