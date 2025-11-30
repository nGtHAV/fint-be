# Fint Backend API

A Django REST Framework backend API for the Fint Finance Tracker application with PostgreSQL database, JWT authentication, and Zoho Mail integration.

## 🚀 Features

- **User Authentication**: Register, login, JWT-based authentication
- **Password Reset**: Email-based password reset via Zoho Mail SMTP (SSL)
- **Receipt Management**: Full CRUD operations for expense receipts
- **Statistics API**: Spending summaries, monthly breakdowns, category analytics
- **Categories**: Predefined spending categories
- **PostgreSQL**: Production-ready database with migrations
- **Gunicorn**: Production WSGI server with auto-scaling workers

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip (Python package manager)

## 🛠️ Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL

Run the included setup script:

```bash
chmod +x setup_postgres.sh
./setup_postgres.sh
```

Or manually create the database:

```bash
sudo -u postgres psql -c "CREATE DATABASE fint_db;"
sudo -u postgres psql -c "CREATE USER fint_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fint_db TO fint_user;"
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://fint_user:your_password@localhost:5432/fint_db

# Security
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True

# CORS (comma-separated origins)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email (Zoho Mail SSL)
EMAIL_HOST_USER=your-email@zoho.com
EMAIL_HOST_PASSWORD=your-zoho-app-password
FRONTEND_URL=http://localhost:3000
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Seed Default Categories

```bash
python seed_data.py
```

### 7. Run the Server

**Development:**
```bash
python manage.py runserver 0.0.0.0:5000
```

**Production with Gunicorn:**
```bash
./start.sh production
```

The API will be available at `http://localhost:5000`

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/forgot-password` | Request password reset email |
| POST | `/api/auth/reset-password` | Reset password with token |

### Receipts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/receipts` | Get all user receipts |
| POST | `/api/receipts` | Create new receipt |
| GET | `/api/receipts/:id` | Get single receipt |
| PUT | `/api/receipts/:id` | Update receipt |
| DELETE | `/api/receipts/:id` | Delete receipt |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats/summary` | Get spending summary |
| GET | `/api/stats/monthly` | Get monthly breakdown |

### Categories & Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | Get all categories |
| PUT | `/api/users/profile` | Update user profile |
| PUT | `/api/users/password` | Change password |
| DELETE | `/api/users/delete` | Delete account |

## 📧 Email Configuration (Zoho Mail)

The backend uses Zoho Mail SMTP with SSL (port 465) for password reset emails:

1. Log into Zoho Mail
2. Go to Settings → Mail Accounts → Generate App Password
3. Add credentials to `.env` file

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --no-input

CMD ["gunicorn", "--config", "gunicorn.conf.py", "fint_backend.wsgi:application"]
```

## 📊 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (False in production) | No |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins | No |
| `EMAIL_HOST_USER` | Zoho Mail email address | Yes |
| `EMAIL_HOST_PASSWORD` | Zoho Mail app password | Yes |
| `FRONTEND_URL` | Frontend URL for email links | No |

## 📁 Project Structure

```
fint-be/
├── apps/
│   ├── categories/     # Category model and views
│   ├── receipts/       # Receipt CRUD and statistics
│   └── users/          # Authentication and profiles
├── fint_backend/
│   ├── settings.py     # Django configuration
│   ├── urls.py         # URL routing
│   └── wsgi.py         # WSGI application
├── manage.py           # Django CLI
├── requirements.txt    # Python dependencies
├── gunicorn.conf.py    # Gunicorn configuration
├── seed_data.py        # Database seeder
├── setup_postgres.sh   # PostgreSQL setup script
└── start.sh            # Server startup script
```

## 📄 License

MIT License
