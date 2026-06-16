# Nexus Attendance Portal

A modern, efficient student attendance management system built with Flask and an SQL database.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### ✨ Core Features
- **QR Code Scanning** - Real-time attendance marking via QR codes using device cameras
- **Manual Entry** - UID-based manual attendance input fallback
- **Live Stats** - Real-time attendance statistics with auto-refresh
- **Dashboards** - Role-based views for Admins, Teachers, and Students
- **Absent Reports** - Identify absentees and export logs to Excel/CSV
- **Email Alerts** - One-click automated absence notifications to parents via SMTP
- **Google Sheets Integration** - Auto-sync attendance directly to Google Sheets

### 💾 Backend
- **Database agnostic** - Supports MySQL and PostgreSQL
- **SQLAlchemy ORM** - Type-safe, secure database operations
- **Auto-migration** - Legacy CSV data automatically migrates to the database on first run
- **RBAC Authentication** - Secure password hashing and role-based access control

### 🎨 Frontend
- **Modern UI** - Dark theme with beautiful glassmorphism design
- **Responsive** - Works seamlessly on desktop, tablet, and mobile
- **Real-time Updates** - Dashboard stats auto-refresh every 10 seconds via API
- **Dynamic State** - QR scanners and settings toggle without requiring page reloads

### 📊 Management Panel
- **Users Tab** - View and manage all enrolled students and teachers
- **Sessions Tab** - Track global attendance sessions by date
- **Support Tab** - Built-in customer support ticketing system
- **Settings Tab** - Configure app preferences (saved directly to DB)

## 🏗️ System Architecture

```mermaid
graph TD
    classDef client fill:#2D3748,stroke:#4A5568,stroke-width:2px,color:#fff
    classDef frontend fill:#3182CE,stroke:#2B6CB0,stroke-width:2px,color:#fff
    classDef backend fill:#38A169,stroke:#2F855A,stroke-width:2px,color:#fff
    classDef database fill:#D69E2E,stroke:#B7791F,stroke-width:2px,color:#fff
    classDef external fill:#805AD5,stroke:#6B46C1,stroke-width:2px,color:#fff
    
    Client["Teacher / Student Device"]:::client
    UI["Frontend Dashboards & jsQR Scanner"]:::frontend
    API["Flask Backend Core & Routing"]:::backend
    DB[("MySQL Database")]:::database
    ExtSMTP["SMTP Mail Server"]:::external
    ExtSheet["Google Sheets API"]:::external
    
    Client -->|Scans QR / Clicks| UI
    UI -->|AJAX POST / Fetch JSON| API
    API <-->|Read / Write Data| DB
    API -->|Dispatch Warning Emails| ExtSMTP
    API -->|Sync Live Logs| ExtSheet
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3, Flask |
| Database | MySQL + SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript (Vanilla), Jinja2 |
| Visualization | Chart.js |
| Hardware API | jsQR (Camera processing) |

## Installation & Setup

### Local Development

1. **Clone Repository**
```bash
git clone https://github.com/your-username/student-attendance-portal.git
cd student-attendance-portal
```

2. **Create Virtual Environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run Application**
```bash
python app.py
```

Visit: `http://localhost:5000`

## Deployment

### Deploy to Render.com (FREE ✨)

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete step-by-step guide.

**Quick Summary:**
1. Push to GitHub
2. Connect GitHub to Render.com
3. Set environment variables
4. Deploy (takes ~2 minutes)

Your app will be live at: `https://nexus-attendance.onrender.com`

## Project Structure

```
student-attendance-portal/
├── app.py                  # Main Flask application & routes
├── requirements.txt        # Python dependencies
├── Procfile               # Render deployment config
├── runtime.txt            # Python version specification
├── DEPLOY.md              # Deployment guide
├── .env.example           # Environment variables template
├── reset_db.py            # Utility script to reset database
│
├── static/                # Static assets (CSS, JS, profile uploads)
├── templates/             # HTML templates
│   ├── base.html          # Master layout
│   ├── login.html         # Authentication interface
│   ├── index.html         # Main attendance marking UI
│   ├── dashboard.html     # Attendance history overview
│   ├── student_dashboard.html # Student attendance view
│   ├── teacher_dashboard.html # Teacher QR scanning interface
│   ├── management.html    # Admin management panel
│   ├── report.html        # Absentee reporting UI
│   └── absentees.html     # Full absentee list view
│
├── email_helper.py        # SMTP Email notification service
├── gsheet_helper.py       # Google Sheets sync integration
├── absent_notifier.py     # Absentee calculation logic
├── cron_task.py           # Automated background scheduled tasks
│
├── students.csv           # Legacy student data (auto-migrated)
├── attendance_log.csv     # Legacy attendance history
├── credentials.json       # Google API credentials
```

## Database Schema (Core Tables)

### Users & Role-Based Auth
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL -- admin, teacher, student
);
```

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE, -- Links to users table
    uid VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255)
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    date VARCHAR(10) NOT NULL,
    time VARCHAR(8) NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id),
    UNIQUE(student_id, date)
);
```

## Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/login` | GET, POST | User authentication & role routing |
| `/student/dashboard` | GET | Student attendance calendar & history |
| `/teacher/dashboard` | GET | Teacher QR scanner & class stats |
| `/management` | GET | Admin panel (Users, Settings, Reports) |
| `/mark_attendance_api` | POST | AJAX endpoint for JS QR scanner |
| `/api/stats` | GET | Real-time widget statistics |
| `/export/<type>` | GET | Export raw logs (csv/excel) |
| `/send_absent_notifications`| POST | Dispatch automated absence emails |

## Configuration

### Environment Variables

```bash
FLASK_ENV=production          # production or development
SECRET_KEY=your-secret-key    # Random secret key
DATABASE_URL=mysql+pymysql://root:password@localhost/db  # DB connection string
GMAIL_USER=your_email@gmail.com # Sender email
GMAIL_PASS=your_app_password  # Sender app password
```

### For Google Sheets Integration

1. Create Google API credentials
2. Download JSON file
3. Save as `credentials.json` in project root
4. Update `gsheet_helper.py` with your spreadsheet ID

## Performance Optimizations

✅ **Database Indexes**
- Student UID (fast lookups during QR scans)
- Attendance date (fast filtering for charts)
- Student ID (fast relational joins)

✅ **Query Efficiency**
- Atomic transactions
- Automatic connection pooling
- Prevents double-marking natively via SQL constraints

✅ **Frontend**
- DOM manipulation instead of page reloads for settings
- LocalStorage for UI theme preferences
- AJAX polling for dashboard data freshness

## Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### Database Connection Issues
- Ensure your SQL database is properly configured for simultaneous connections.

### CSV Migration Not Working
- Ensure `students.csv` is in project root.
- Run: `python app.py`. Legacy data is parsed and inserted into the SQL tables automatically on startup.

### Google Sheets Not Syncing
- Check `credentials.json` exists and is valid.
- Verify spreadsheet ID in `gsheet_helper.py`.

## Future Enhancements

- [ ] PostgreSQL support for scalability
- [ ] Multi-class/batch management
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Biometric attendance (fingerprint)
- [ ] Automated SMS alerts
- [ ] Payment integration for fees

## Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact the development team

## Changelog

### v1.0.0 (April 4, 2026)
- ✅ Initial release
- ✅ CSV to SQL migration
- ✅ Real-time statistics & Chart.js integration
- ✅ QR code scanning via device camera
- ✅ Multi-role dashboards (Admin, Teacher, Student)
- ✅ Render.com deployment ready

---

**Made with ❤️ for better attendance management**

Visit: [Nexus Attendance Portal](https://nexus-attendance.onrender.com)
