# Connectly

Connectly is a social media API project developed for our Integrative Programming and Technologies class. It is built using Django and Django REST Framework.

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
- Django REST Framework
- SQLite
- Postman for API testing

## Project Structure
- `users/` – user management and roles
- `posts/` – posts, feed, likes, comments, follow system
- `connectly_project/` – main project configuration

## Setup Instructions
1. Clone the repository
2. Open the project folder
3. Create and activate a virtual environment
4. Install dependencies
5. Run migrations
6. Start the development server

## Sample Commands
```bash
python manage.py migrate
python manage.py runserver
