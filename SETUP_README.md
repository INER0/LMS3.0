# 📚 Library Management System (LMS 2.0)

A comprehensive Django-based Library Management System with modern UI and advanced features for academic coursework.

## 🚀 Features

### 🔐 Authentication & Security
- **Multi-role User System**: Members, Librarians, Managers, Admin
- **Secure Authentication**: MFA support and audit logging
- **Session Management**: Automatic timeout and security controls
- **Password Policies**: Enforced strong password requirements

### 📖 Library Management
- **Multi-branch Operations**: Comprehensive book management across multiple library branches
- **Book Catalog**: Advanced search, categorization, and inventory tracking
- **Digital Integration**: Support for digital resources and services
- **Real-time Availability**: Live tracking of book availability and reservations

### 🔄 Circulation System
- **Book Borrowing**: Automated lending with due date management
- **Reservations**: Priority-based reservation system
- **Fine Management**: Automated fine calculation and payment processing
- **Extension System**: Book loan extensions with proper authorization

### 💳 Payment Processing
- **Membership Fees**: Multiple membership tiers (Basic MVR 50/month, Premium MVR 75/month, Student MVR 30/month)
- **Fine Payments**: Multiple payment methods (Cash, Card, Online Banking, Mobile Payment)
- **Digital Services**: Payment integration for additional library services
- **Payment History**: Comprehensive transaction tracking and reporting

### 📊 Analytics & Reporting
- **Revenue Analytics**: Daily and monthly revenue tracking
- **Usage Statistics**: Book borrowing patterns and user behavior
- **Management Reports**: Comprehensive reports for library managers
- **Export Features**: CSV and PDF report generation

### 🎨 Modern UI/UX
- **Glass-morphism Design**: Modern, elegant interface with backdrop blur effects
- **Responsive Layout**: Mobile-first design that works on all devices
- **Dark Theme**: Eye-friendly dark color scheme
- **Interactive Elements**: Smooth animations and transitions

## 🛠️ Technical Stack

- **Backend**: Django 5.2.5 (Python 3.13)
- **Database**: SQLite (easily switchable to PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5 + Custom CSS with Glass-morphism effects
- **Icons**: Font Awesome 6
- **Authentication**: Django's built-in authentication with custom extensions

## 📋 Prerequisites

Before running this project, make sure you have:

- Python 3.11+ installed
- pip (Python package installer)
- Git (for cloning the repository)

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/INER0/LMS3.0.git
cd LMS3.0
```

### 2. Create Virtual Environment
```bash
python -m venv lms_env

# Activate virtual environment
# On macOS/Linux:
source lms_env/bin/activate
# On Windows:
lms_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Apply migrations
python manage.py migrate

# Load initial data (optional - includes sample books, users, etc.)
python manage.py loaddata db_backup_20250809_154233.json

# Create database views for analytics
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    # Create monthly_revenue view
    cursor.execute('''
        CREATE VIEW monthly_revenue AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY month) as id,
            month,
            COALESCE(membership_revenue, 0) as membership_revenue,
            COALESCE(fine_revenue, 0) as fine_revenue,
            COALESCE(service_revenue, 0) as service_revenue,
            COALESCE(reservation_revenue, 0) as reservation_revenue,
            COALESCE(membership_revenue, 0) + COALESCE(fine_revenue, 0) + COALESCE(service_revenue, 0) + COALESCE(reservation_revenue, 0) as total_revenue
        FROM (
            SELECT 
                DATE(payment_date, \"start of month\") as month,
                SUM(CASE WHEN purpose = \"membership\" THEN amount ELSE 0 END) as membership_revenue,
                SUM(CASE WHEN purpose = \"fine\" THEN amount ELSE 0 END) as fine_revenue,
                SUM(CASE WHEN purpose = \"digital\" THEN amount ELSE 0 END) as service_revenue,
                SUM(CASE WHEN purpose = \"reservation\" THEN amount ELSE 0 END) as reservation_revenue
            FROM payments
            WHERE status = \"completed\"
            GROUP BY DATE(payment_date, \"start of month\")
        );
    ''')
    
    # Create daily_revenue view
    cursor.execute('''
        CREATE VIEW daily_revenue AS
        SELECT 
            ROW_NUMBER() OVER (ORDER BY date) as id,
            date,
            total_amount,
            transaction_count
        FROM (
            SELECT 
                DATE(payment_date) as date,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count
            FROM payments
            WHERE status = \"completed\"
            GROUP BY DATE(payment_date)
        );
    ''')
    
    print('Database views created successfully!')
"
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Collect Static Files (for production)
```bash
python manage.py collectstatic --noinput
```

## 🚀 Running the Application

### Development Server
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

### Default Accounts (if using sample data)
- **Admin**: admin / admin123
- **Manager**: manager / manager123  
- **Librarian**: librarian / librarian123
- **Member**: member / member123

## 📁 Project Structure

```
lms2.0/
├── authentication/         # User management and authentication
├── library/                # Book management and library operations
├── circulation/            # Book loans, reservations, fines
├── payments/               # Payment processing and membership fees
├── api/                    # API endpoints (future expansion)
├── templates/              # HTML templates
│   ├── base.html          # Base template with glass-morphism design
│   ├── authentication/    # Auth-related templates
│   ├── library/           # Library management templates
│   ├── circulation/       # Circulation system templates
│   └── payments/          # Payment system templates
├── static/                 # Static files (CSS, JS, images)
├── logs/                   # Application logs
├── fixtures/               # Sample data files
├── db_backup_*.json       # Database backup files
├── requirements.txt       # Python dependencies
└── manage.py              # Django management script
```

## 🎯 Key URLs

- **Home**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **Library Dashboard**: `http://127.0.0.1:8000/library/`
- **Staff Management**: `http://127.0.0.1:8000/library/manager/staff/`
- **Payment System**: `http://127.0.0.1:8000/payments/membership/`
- **Circulation**: `http://127.0.0.1:8000/circulation/`

## 📊 Sample Data

The database backup includes:
- **31 Books** with multiple copies across 4 branches
- **16 Users** with different roles (Admin, Manager, Librarian, Members)
- **42 Book Loans** with various statuses
- **5 Payments** demonstrating the payment system
- **3 Fine Records** showing fine management
- **4 Library Branches** with sections

## 🎨 UI Features

### Glass-morphism Design
- Semi-transparent cards with backdrop blur
- Gradient borders and hover effects
- Modern color palette with dark theme
- Smooth animations and transitions

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimized layouts
- Touch-friendly interface elements
- Accessible design patterns

## 🔧 Customization

### Membership Plans
Edit `templates/payments/membership.html` to modify:
- Pricing (currently MVR 50/75/30 for Basic/Premium/Student)
- Features included in each plan
- Payment methods available

### Library Settings
Modify `library/models.py` for:
- Book categories
- Branch management
- Fine calculation rules
- Loan periods

### UI Theme
Update `templates/base.html` and custom CSS for:
- Color schemes
- Glass-morphism effects
- Layout adjustments
- Brand customization

## 🚨 Important Notes

### Files NOT in Git
These files are intentionally excluded from version control:
- **Logs**: `logs/` directory (contains runtime logs)
- **Static Files**: `static/` and `staticfiles/` (generated files)
- **Database**: `db.sqlite3` (contains user data)
- **Virtual Environment**: `lms_env/` (local Python environment)

### Required Manual Setup
1. **Database Views**: Must be created after loading data (see setup instructions)
2. **Virtual Environment**: Create locally for each installation
3. **Static Files**: Run `collectstatic` for production deployment
4. **Secret Key**: Update `settings.py` with new secret key for production

## 🐛 Troubleshooting

### Common Issues

1. **Database Views Missing**
   ```bash
   # Run the database view creation script from setup instructions
   ```

2. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Permission Errors**
   - Ensure proper file permissions
   - Check virtual environment activation

4. **Port Already in Use**
   ```bash
   python manage.py runserver 8001  # Use different port
   ```

## 📝 Development Notes

### Recent Updates
- ✅ Fixed staff management role display issues
- ✅ Updated membership pricing (Basic MVR 50, Premium MVR 75, Student MVR 30)
- ✅ Simplified staff management to delete-only functionality
- ✅ Created database backup with all sample data
- ✅ Fixed database view creation for analytics

### Future Enhancements
- [ ] API endpoints for mobile app integration
- [ ] Email notification system
- [ ] Advanced reporting dashboard
- [ ] Multi-language support
- [ ] Integration with external library systems

## 🤝 Contributing

This project is part of academic coursework. For contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is created for educational purposes as part of academic coursework.

## 📞 Support

For support or questions about this project, please refer to the academic course materials or contact your instructor.

---

**Created with ❤️ using Django 5.2.5 and modern web technologies**
