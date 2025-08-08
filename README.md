# Library Management System (LMS 2.0)

A comprehensive Django-based Library Management System designed for academic institutions, featuring modern web interface, role-based access control, and complete circulation management.

## 🚀 Features

### Core Functionality
- **Multi-branch Library Operations** - Support for multiple library branches
- **Advanced Book Management** - Complete catalog with authors, publishers, categories
- **Circulation System** - Book borrowing, returns, reservations, and renewals
- **Fine Management** - Automated fine calculations and payment processing
- **User Management** - Role-based access control (Members, Librarians, Managers, Admin)

### Security & Authentication
- **Secure Authentication** with session management
- **Role-based Access Control (RBAC)** with proper permissions
- **Account Security** - Password policies, account locking, audit logging
- **Multi-Factor Authentication (MFA)** ready infrastructure

### Modern Interface
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Glass Morphism UI** - Modern, elegant interface with gradient backgrounds
- **Intuitive Navigation** - Easy-to-use sidebar and navigation system
- **Real-time Statistics** - Dashboard with live data and charts

### Payment System
- **Membership Fee Management** - Multiple membership tiers
- **Fine Payment Processing** - Automated fine calculation and payment
- **Payment History** - Complete transaction records

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2.5 (Python)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5.3.0 with custom CSS
- **Authentication**: Django's built-in auth with custom extensions
- **API**: Django REST Framework ready

### Apps Structure
```
lms2.0/
├── authentication/     # User management, roles, security
├── library/           # Books, authors, publishers, branches
├── circulation/       # Loans, reservations, fines
├── payments/          # Payment processing, membership fees
└── api/              # REST API endpoints
```

## 💰 Membership Structure

| Membership Type | Monthly Fee | Annual Fee | Max Books | Loan Period |
|----------------|-------------|------------|-----------|-------------|
| **Basic Member** | MVR 50 | MVR 500 | 3 Books | 14 Days |
| **Premium Member** | MVR 75 | MVR 750 | 5 Books | 14 Days + 7 Days Extension |
| **Student Member** | MVR 30 | MVR 300 | 4 Books | 21 Days |

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd lms2.0
```

2. **Create virtual environment**
```bash
python -m venv lms_env
source lms_env/bin/activate  # On Windows: lms_env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixtures/initial_data.json
```

5. **Create admin user**
```bash
python manage.py createsuperuser
```

6. **Assign membership fees to users**
```bash
python manage.py assign_membership --membership-type basic
```

7. **Run development server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

### Demo Users
The system includes demo users for testing:
- **Student**: `student@library.edu` / `demo123`
- **Librarian**: `librarian@library.edu` / `demo123`
- **Admin**: `admin@library.edu` / `demo123`

## 📱 Usage

### For Library Members
1. **Register/Login** - Create account or use demo credentials
2. **Browse Books** - Search and filter the library catalog
3. **Borrow Books** - Click on available books to borrow
4. **Manage Loans** - View current loans, due dates, and extend if eligible
5. **Reservations** - Reserve books that are currently unavailable
6. **Pay Fines** - View and pay any outstanding fines

### For Library Staff
1. **Manage Books** - Add, edit, and organize the book catalog
2. **Circulation Management** - Handle loans, returns, and reservations
3. **User Management** - Manage member accounts and permissions
4. **Reports & Analytics** - View system statistics and reports

## 🔧 Management Commands

```bash
# Assign membership fees to users
python manage.py assign_membership --membership-type basic

# Update membership fee structure
python manage.py update_membership_fees

# Fix loan due dates after membership changes
python manage.py fix_loan_dates

# Create demo users
python manage.py assign_membership
```

## 🎨 Customization

### Themes & Styling
The system uses a modern glass morphism design with:
- Custom gradient backgrounds
- Translucent cards and modals
- Responsive Bootstrap components
- Font Awesome icons

### Configuration
Key settings can be customized in `settings.py`:
- Database configuration
- Static files handling
- Security settings
- Email configuration (for notifications)

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up static file serving
- [ ] Configure email backend
- [ ] Set up proper logging
- [ ] Configure HTTPS
- [ ] Set up backup system

### Environment Variables
Create a `.env` file for production settings:
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review existing issues and discussions

## 📈 Roadmap

- [ ] Mobile app development
- [ ] Advanced reporting dashboard
- [ ] Email notifications
- [ ] QR code integration
- [ ] Multi-language support
- [ ] API documentation with Swagger

---

**Built with ❤️ using Django**
