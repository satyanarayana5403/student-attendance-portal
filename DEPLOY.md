# Deploy to Render.com

## Step 1: Delete Old Service (if exists)
Go to Render dashboard → Delete the old `student-attendance-portal` service

## Step 2: Create New Web Service
1. Go to https://dashboard.render.com/new/web
2. Select repository: `student-attendance-portal`
3. Fill form:
   - **Name**: `student-attendance-portal`
   - **Environment**: Python 3.12 (select from dropdown)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

## Step 3: Add Environment Variables
Click "Advanced" → Add these:
```
FLASK_ENV = production
SECRET_KEY = (generate with: python -c "import secrets; print(secrets.token_hex(32))")
```

## Step 4: Deploy
Click "Create Web Service" and wait 2-3 minutes

## Your App URL
```
https://student-attendance-portal.onrender.com
```

---

## Notes
- Free tier has 15-minute idle timeout = cold starts (5-10s)
- MySQL/PostgreSQL works fine for small deployments
- For upgrades/issues, check Render logs in dashboard
