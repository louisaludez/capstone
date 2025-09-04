# Hotel Management System (HMS)

A comprehensive Hotel Management System built with Django, featuring multiple modules for managing various aspects of hotel operations.

## Features

- User Authentication and Authorization
- Staff Management
- Room Service Management
- Restaurant and Cafe Management
- Laundry Service
- Concierge Services
- Real-time Chat System
- Food and Beverage (F&B) Management
- Admin Dashboard
- API Integration

## Technology Stack

- **Backend Framework**: Django 5.2
- **Database**: MySQL
- **Real-time Communication**: Django Channels (Daphne)
- **API Framework**: Django REST Framework
- **Authentication**: Custom User Model
- **Frontend**: HTML, CSS, JavaScript
- **Static Files**: Django Static Files

## Project Structure

```
├── api/                 # API endpoints
├── cafe/               # Cafe management module
├── chat/               # Real-time chat system
├── concierge/          # Concierge services
├── fnb/                # Food and Beverage management
├── globals/            # Global utilities and functions
├── hmsAdmin/           # Admin dashboard
├── hotelAi/            # Main project configuration
├── laundry/            # Laundry service management
├── myHotel/            # Core hotel management
├── restaurant/         # Restaurant management
├── room_service/       # Room service management
├── staff/              # Staff management
├── static/             # Static files (CSS, JS, Images)
└── users/              # User management and authentication
```

## Prerequisites

- Python 3.x
- MySQL Server
- Virtual Environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [project-directory]
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure MySQL database:
- Create a database named 'hotelai'
- Update database settings in `hotelAi/settings.py` if needed

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Configuration

The main configuration file is located at `hotelAi/settings.py`. Key configurations include:

- Database settings
- Static files configuration
- Installed apps
- Middleware settings
- Authentication settings

## Usage

1. Access the admin interface at `/admin`
2. Login with your superuser credentials
3. Navigate through different modules:
   - Staff Management
   - Room Service
   - Restaurant/Cafe
   - Laundry Service
   - Concierge Services
   - F&B Management

## Documentation

- See `docs/README.md` for the full API and component documentation.
- Start with `docs/routes.md` and `docs/auth.md`.

## Security

- Custom user model implementation
- Django's built-in security features
- CSRF protection
- Session management
- Password validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

