# 🚀 Quick Start Guide

## 🎯 What's New

✨ **Complete LMS System with:**
- Admin & Student Dashboards
- JWT Authentication
- File Versioning
- Dark Premium Theme
- Fully Connected Frontend

---

## ⚡ Quick Setup (5 minutes)

### Backend Setup

**Terminal 1:**
```bash
cd /Users/manjotsingh/Downloads/New_/VC_Lms

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start backend server
uvicorn main:app --reload
```

✅ Backend running at: http://localhost:8000
📖 Interactive API docs: http://localhost:8000/docs

### Frontend Setup

**Terminal 2:**
```bash
cd /Users/manjotsingh/Downloads/New_/VC_Lms/frontend

# Install dependencies
npm install

# Start frontend dev server
npm run dev
```

✅ Frontend running at: http://localhost:3000

---

## 🔐 Test Credentials

### Admin Login
- **Username:** `admin`
- **Password:** `1234`

### Student Login
- **Name:** Any name (e.g., "John Doe")
- **URN:** Any URN (e.g., "S12345")

---

## 🎨 Features to Try

### 👨‍💼 Admin Dashboard
- Search students by name or URN
- View all student files
- Download any file version

### 👨‍🎓 Student Dashboard
- Upload files with comments
- View version history
- Download latest versions

---

## 📁 Project Structure

```
Backend:
├── main.py                 # FastAPI app
├── routes/
│   ├── auth.py            # JWT authentication
│   └── files.py           # File management
├── models.py              # Database models
├── database.py            # DB config
└── .env                   # Configuration

Frontend (Vue 3 + Vite):
├── src/
│   ├── App.vue            # Main app
│   ├── views/             # Pages
│   ├── components/        # UI components
│   └── services/
│       └── api.js         # Backend API client
└── style.css              # Dark theme
```

---

## 🔗 API Endpoints

### Authentication
```
POST   /auth/admin/login       - Admin login
POST   /auth/student/login     - Student login
GET    /auth/verify            - Verify token
```

### Student Endpoints
```
POST   /files/upload           - Upload file
GET    /files/my               - Get my files
GET    /files/my/latest        - Download latest
```

### Admin Endpoints
```
GET    /files/admin/search     - Search students
GET    /files/admin/files      - Get student files
GET    /files/admin/download   - Download file
```

---

## 🧪 Testing with curl

### Admin Login
```bash
curl -X POST "http://localhost:8000/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "1234"}'
```

### Student Login
```bash
curl -X POST "http://localhost:8000/auth/student/login" \
  -H "Content-Type: application/json" \
  -d '{"student_name": "John Doe", "student_urn": "S12345"}'
```

### Upload File
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "comment=My assignment"
```

---

## 🐛 Troubleshooting

**Backend won't start?**
```bash
# Check if port 8000 is in use
lsof -i :8000
# Use different port
uvicorn main:app --port 8001
```

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Check browser console (F12) for errors
- Verify CORS is enabled

**Database errors?**
```bash
# Reset database
rm test.db
python init_db.py
```

---

## 📚 Full Documentation

See **SETUP.md** for comprehensive setup guide and troubleshooting.

---

## 🚢 Production Build

### Backend
```bash
pip install gunicorn
gunicorn main:app --workers 4
```

### Frontend
```bash
cd frontend
npm run build
# Output: dist/ folder (ready to deploy)
```

### Get Latest Version
```bash
curl "http://127.0.0.1:8000/latest/?student_urn=URN123456&filename=myfile.txt"
```

### Download Latest File
```bash
curl "http://127.0.0.1:8000/download/latest/?student_urn=URN123456&filename=myfile.txt" -O
```

### View All Files (Admin)
```bash
curl "http://127.0.0.1:8000/admin/files/"
```

---

## File Storage
- Uploaded files are stored in: `./uploads/` directory
- File naming format: `{student_urn}_{filename}_v{version}`
- Example: `URN123456_essay.txt_v1`

---

## Database Schema
**Table: files**
- id (Integer, Primary Key)
- filename (String)
- version (Integer)
- filepath (String)
- student_name (String, lowercase)
- student_urn (String, unique identifier)
- comment (String)
- uploaded_at (DateTime)

---

## All Issues Fixed ✅
See [FIXES_SUMMARY.md](FIXES_SUMMARY.md) for detailed changes.
