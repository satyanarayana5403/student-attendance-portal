# Nexus Attendance Portal

A modern, efficient student attendance management system built with Flask and SQLite.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### ✨ Core Features
- **QR Code Scanning** - Real-time attendance marking via QR codes
- **Manual Entry** - UID-based manual attendance input
- **Live Stats** - Real-time attendance statistics with auto-refresh
- **Dashboard** - Comprehensive attendance history with date grouping
- **Absent Reports** - Identify absentees and export to Excel/PDF
- **Email Alerts** - Notify parents of absences
- **Google Sheets Integration** - Auto-sync attendance to Google Sheets

### 💾 Backend
- **SQLite Database** - Efficient indexed queries
- **SQLAlchemy ORM** - Type-safe database operations
- **Auto-migration** - CSV data automatically migrates to database
- **Data Cleanup** - Auto-delete records older than 30 days

### 🎨 Frontend
- **Modern UI** - Dark theme with glassmorphism design
- **Responsive** - Works on desktop, tablet, and mobile
- **Real-time Updates** - Stats refresh every 10 seconds
- **Tab Navigation** - Persistent tabs with localStorage

### 📊 Management Panel
- **Students Tab** - View all enrolled students with emails
- **Sessions Tab** - Track attendance sessions by date
- **Settings Tab** - Configure app preferences
- **Persistent State** - Settings saved to browser storage

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask 3.0.3 |
| Database | SQLite + SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Server | Gunicorn |
| Hosting | Render.com (Free) |

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
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Procfile               # Render deployment config
├── render.yaml            # Render web service config
├── runtime.txt            # Python version specification
│
├── templates/             # HTML templates
│   ├── index.html         # Mark attendance page
│   ├── dashboard.html     # Attendance history
│   ├── report.html        # Absent report
│   ├── management.html    # Admin panel
│   └── absentees.html     # Absentees list
│
├── email_helper.py        # Email notification service
├── gsheet_helper.py       # Google Sheets integration
├── cron_task.py           # Scheduled tasks
│
├── students.csv           # Student data (auto-migrated)
├── attendance_log.csv     # Attendance history (auto-migrated)
├── attendance.db          # SQLite database (auto-created)
│
└── credentials.json       # Google API credentials
```

## Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    uid VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX(uid)
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    date VARCHAR(10) NOT NULL,
    time VARCHAR(8) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    UNIQUE(student_id, date),
    INDEX(date),
    INDEX(student_id)
);
```

## Key Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET, POST | Home - Mark attendance |
| `/dashboard` | GET | Attendance history |
| `/report` | GET | Absent students report |
| `/management` | GET | Admin panel (Students, Sessions, Settings) |
| `/mark_attendance_api` | POST | API for marking attendance |
| `/get_stats` | GET | Real-time statistics |
| `/report/export/<type>` | GET | Export report (excel/pdf) |
| `/send-emails` | GET | Send absence notifications |

## Configuration

### Environment Variables

```bash
FLASK_ENV=production          # production or development
SECRET_KEY=your-secret-key    # Random secret key
DATABASE_URL=sqlite:///attendance.db  # Database connection
PORT=5000                     # Port number
```

### For Google Sheets Integration

1. Create Google API credentials
2. Download JSON file
3. Save as `credentials.json` in project root
4. Update `gsheet_helper.py` with your spreadsheet ID

## Performance Optimizations

✅ **Database Indexes**
- Student UID (fast lookups)
- Attendance date (fast filtering)
- Student ID (fast joins)

✅ **Query Efficiency**
- Direct database queries (no CSV reads)
- Atomic transactions
- Automatic connection pooling

✅ **Frontend**
- Lazy tab loading
- LocalStorage for settings
- Auto-refresh (10 seconds)

## Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### Database Lock Issues
- SQLite shouldn't have issues with small user count
- For production use, upgrade to PostgreSQL on Render

### CSV Migration Not Working
- Ensure `students.csv` and `attendance_log.csv` are in project root
- Run: `python app.py` (migration happens automatically)

### Google Sheets Not Syncing
- Check `credentials.json` exists and is valid
- Verify spreadsheet ID in `gsheet_helper.py`

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
- ✅ CSV to SQLite migration
- ✅ Real-time statistics
- ✅ QR code scanning
- ✅ Management panel with tabs
- ✅ Render.com deployment ready

---

**Made with ❤️ for better attendance management**

Visit: [Nexus Attendance Portal](https://nexus-attendance.onrender.com)
