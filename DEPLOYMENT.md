# Deployment Guide: Render.com

## Quick Start (5 minutes)

### Step 1: Push Code to GitHub

```bash
# In your project directory
git init
git add .
git commit -m "Initial commit: Attendance portal with SQL database"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/student-attendance-portal.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account (easier)

### Step 3: Create New Web Service
1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Select your `student-attendance-portal` repository

### Step 4: Configure Service

**Name:** `nexus-attendance`

**Environment:** `Python`

**Build Command:** 
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn app:app
```

**Plan:** Free (available)

### Step 5: Add Environment Variables

In the **Environment** section, add:

```
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here
```

Generate a secret key by running in Python:
```python
import secrets
print(secrets.token_hex(16))
```

### Step 6: Deploy

Click **Create Web Service** and wait 2-3 minutes for deployment.

Your app will be live at: `https://nexus-attendance.onrender.com`

---

## Features Available on Free Tier

✅ Python Flask apps  
✅ SQLite database (works fine for small projects)  
✅ 512 MB RAM  
✅ Automatic deployments from GitHub  
✅ HTTPS/SSL included  
✅ Custom domain support  

⚠️ **Note:** Free tier has a cold start (takes longer on first request after inactivity)

---

## Important Notes

### Database
- SQLite database file persists within the instance
- If you need persistent data across re-deployments, upgrade to paid plan or use PostgreSQL

### For Production Use
If you want to scale beyond free tier:

1. **Upgrade to Paid** (Render has affordable pricing)
2. **Or Use PostgreSQL** (Render offers free PostgreSQL)

To switch to PostgreSQL:
- Create a PostgreSQL database on Render
- Copy the connection URL
- The app will automatically use it (already configured)

### File Uploads/QR Codes
- PDF files are generated in `/tmp` (cleared on restart)
- For persistent file storage, implement cloud storage (AWS S3, etc.)

---

## Troubleshooting

### "Module not found" error
- Check if all dependencies are in `requirements.txt`
- Run: `pip freeze > requirements.txt` locally

### Database issues
- Render may use a read-only filesystem for SQLite
- Upgrade to paid plan or switch to PostgreSQL

### App times out
- Some students.csv migration may take time
- Check Logs in Render dashboard

---

## Next Steps

1. **Custom Domain** (optional)
   - Go to Settings → Custom Domain
   - Add your domain (requires DNS configuration)

2. **Environment Variables** (important)
   - Update `SECRET_KEY` to a strong value
   - Add `GOOGLE_CREDENTIALS` if using Google Sheets

3. **Monitoring**
   - Check Render dashboard for logs
   - Monitor resource usage

4. **Updates**
   - Push changes to GitHub
   - Render automatically re-deploys

---

## Still Free? 🎉

- **Render.com** has a genuinely free tier
- No credit card required initially
- Pay only when you upgrade

Enjoy your live attendance portal!
