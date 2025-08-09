# 📚 Library Management System (LMS 3.0)

A comprehensive Django-based Library Management System with modern UI, multi-branch operations, and advanced security features designed for academic coursework.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)
![License](https://img.shields.io/badge/License-Academic-yellow.svg)

## 🚀 Quick Start

### 📋 Prerequisites
- **Python 3.8+** (Python 3.9+ recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository)

### ⚡ Installation (3 Methods)

#### Method 1: Complete Setup (Recommended)
```bash
# 1. Clone the repository
git clone https://github.com/INER0/LMS3.0.git
cd LMS3.0

# 2. Create and activate virtual environment
python -m venv lms_env

# Windows:
lms_env\Scripts\activate

# macOS/Linux:
source lms_env/bin/activate

# 3. Install all requirements
pip install -r requirements.txt

# 4. Setup database
python manage.py migrate
python manage.py loaddata db_backup_20250809_163543.json

# 5. Create demo accounts
python manage.py create_demo_accounts

# 6. Run the server
python manage.py runserver
```

#### Method 2: Minimal Setup (If you encounter dependency issues)
```bash
# Install only essential packages
pip install Django==5.2.5
pip install djangorestframework==3.16.1
pip install python-decouple==3.8
pip install Pillow==11.3.0
pip install django-debug-toolbar==6.0.0
pip install django-extensions==4.1

# Then continue with database setup...
python manage.py migrate
python manage.py loaddata db_backup_20250809_163543.json
python manage.py runserver
```

#### Method 3: Super Simple Setup (Alternative settings)
```bash
# Use simplified settings file
python manage.py runserver --settings=settings_simple

# This bypasses some dependency issues
```

### 🌐 Access the System
- **Main URL**: http://127.0.0.1:8000/ → **Library Dashboard**
- **Login Page**: http://127.0.0.1:8000/auth/login/ → **Universal login for all users**
- **Django Admin**: http://127.0.0.1:8000/admin/ → **Admin backend (for super admins)**

### 🔄 Login Flow
1. **All users login** at: http://127.0.0.1:8000/auth/login/
2. **After login**:
   - **Super Admins** (`admin`, `demo_admin`) → Redirected to `/admin/`
   - **All other users** (Member, Librarian, Manager) → Redirected to `/library/`
3. **Root URL** (http://127.0.0.1:8000/) → Always redirects to `/library/`

## 🎭 Demo Accounts

### 👤 Library Users
| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Member** | `demo_member` | `demo123` | Book browsing, borrowing, profile |
| **Librarian** | `demo_librarian` | `demo123` | Circulation, member management |
| **Manager** | `demo_manager` | `demo123` | Staff management, reports, analytics |

### 🔧 System Administration
| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | `demo_admin` | `demo123` | Django admin backend |
| **Super Admin** | `admin` | `admin123` | Full system control |

> 📄 **Complete credentials list**: See [`LOGIN_CREDENTIALS.txt`](LOGIN_CREDENTIALS.txt)

## ✨ Features

### 🏢 Multi-Branch Operations
- **4 Library Branches**: Male', Kulhudhufushi, Addu City, Research
- **Cross-branch book management** with centralized inventory
- **Branch-specific reports** and analytics

### 📚 Comprehensive Book Management
- **31+ Books** across Fiction, Non-Fiction, Science, History
- **Advanced search** by title, author, ISBN, category
- **Real-time availability** tracking
- **Reservation system** with priority queuing

### 👥 Role-Based User Management
- **4 User Roles** with distinct permissions
- **Secure authentication** with session management
- **Staff management** interface for administrators
- **Member profiles** with borrowing history

### 💳 Advanced Payment System
| Membership Type | Monthly Fee | Max Books | Loan Period | Benefits |
|-----------------|-------------|-----------|-------------|----------|
| **Basic** | MVR 50 | 3 books | 14 days | Standard access |
| **Premium** | MVR 75 | 5 books | 14 days + 7 extension | Priority support |
| **Student** | MVR 30 | 4 books | 21 days | Educational discount |

### 📊 Analytics & Reporting
- **Dashboard analytics** with Chart.js visualizations
- **Revenue tracking** with daily/monthly reports  
- **Borrowing statistics** and trends
- **Overdue management** with automated fine calculation

### 🎨 Modern UI/UX
- **Glass-morphism design** with backdrop blur effects
- **Responsive layout** optimized for all devices
- **Dark theme** with elegant color scheme
- **Interactive elements** with smooth animations

## 🔒 Security Features

### 🛡️ Authentication & Authorization
- **Role-Based Access Control (RBAC)**
- **Secure password policies** (8+ chars, mixed case, numbers)
- **Account lockout protection** (5 failed attempts)
- **Session timeout** (30 minutes inactivity)

### 🔐 Data Protection
- **CSRF protection** on all forms
- **XSS filtering** and content type protection
- **Secure headers** and frame options
- **Comprehensive audit logging**

## 🛠️ Technical Stack

- **Backend**: Django 5.2.5 (Python 3.8+)
- **Database**: SQLite (easily upgradeable to PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5 + Custom CSS with Glass-morphism
- **Charts**: Chart.js for analytics visualization
- **Icons**: Font Awesome 6
- **Authentication**: Django built-in with custom extensions

## 🧪 Testing & Sample Data

### 📊 Included Test Data
- **31 Books** with multiple copies and categories
- **16 Users** across all roles with realistic profiles
- **42 Book Loans** showing complete circulation workflows
- **Payment History** demonstrating all transaction types
- **Fine Records** covering various penalty scenarios

### 🔄 Resetting Data
```bash
# Reset to original sample data
python manage.py flush --noinput
python manage.py migrate
python manage.py loaddata db_backup_20250809_163543.json
python manage.py create_demo_accounts
```

## 📁 Project Structure

```
LMS3.0/
├── authentication/          # User management & security
├── library/                # Core library operations
├── circulation/            # Book lending system
├── payments/               # Payment processing
├── api/                    # REST API endpoints
├── templates/              # HTML templates
├── static/                 # CSS, JavaScript, images
├── fixtures/               # Sample data files
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── LOGIN_CREDENTIALS.txt   # Demo account credentials
├── SETUP_README.md        # Detailed setup guide
└── db_backup_*.json       # Database backups
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### "No module named 'decouple'"
```bash
pip install python-decouple
# OR use alternative settings:
python manage.py runserver --settings=settings_simple
```

#### "No module named 'rest_framework'"
```bash
pip install djangorestframework
```

#### Database Issues
```bash
python manage.py migrate
python manage.py loaddata db_backup_20250809_163543.json
```

#### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

#### Permission/Import Errors
```bash
# Ensure virtual environment is activated
source lms_env/bin/activate  # macOS/Linux
lms_env\Scripts\activate     # Windows

# Verify Python version
python --version  # Should be 3.8+
```

### 🔧 Alternative Setup Options

If you encounter persistent dependency issues:

1. **Use simplified settings**: `--settings=settings_simple`
2. **Install packages individually**: See Method 2 above
3. **Create fresh virtual environment**: Delete `lms_env` and recreate
4. **Check Python version**: Ensure 3.8+ compatibility

## 📚 Documentation

- **[`SETUP_README.md`](SETUP_README.md)** - Comprehensive setup guide
- **[`LOGIN_CREDENTIALS.txt`](LOGIN_CREDENTIALS.txt)** - All demo accounts
- **Code Documentation** - Extensive inline comments and docstrings
- **API Documentation** - Available at `/api/` endpoints

## 🎯 Academic Compliance

This project fulfills all requirements for Advanced Software Development coursework:

### ✅ Part I - Analysis & Design (40%)
- **Use Case Diagrams**: Complete user story coverage
- **Class Diagrams**: Comprehensive OOP model relationships  
- **Sequence Diagrams**: Detailed interaction flows

### ✅ Part II - Implementation & Testing (60%)
- **Agile Development**: Iterative development with Git history
- **Complete Implementation**: All specified features working
- **Comprehensive Testing**: Demo accounts and sample data
- **Security Implementation**: RBAC, authentication, data protection
- **Professional Documentation**: Setup guides and code comments

## 📈 Performance & Scalability

- **Database Optimization**: Efficient queries with proper indexing
- **Static File Management**: Optimized CSS/JS delivery
- **Session Management**: Secure and efficient user sessions
- **Logging System**: Comprehensive error tracking and debugging

## 🤝 Contributing

This is an academic project, but contributions for educational purposes are welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is created for **educational purposes** as part of academic coursework. All code is original work designed to demonstrate professional Django development capabilities.

## 🏆 Project Highlights

- ✅ **Production-ready** Django application
- ✅ **Modern UI/UX** with glass-morphism design
- ✅ **Complete security** implementation
- ✅ **Comprehensive testing** with sample data
- ✅ **Professional documentation**
- ✅ **Academic specification compliance**

## 📞 Support

For technical support or questions:

1. **Check troubleshooting section** above
2. **Review error logs** in `logs/lms.log`
3. **Verify dependencies** with `pip list`
4. **Use demo accounts** for testing functionality

---

**📝 Note**: This Library Management System demonstrates enterprise-level Django development with comprehensive security features, modern UI design, and professional code organization suitable for academic assessment and real-world deployment.

**⚡ Quick Test**: After setup, visit http://127.0.0.1:8000/ and login with `demo_member`/`demo123` to explore the system!

---
*Created with ❤️ using Django 5.2.5 and modern web technologies*
