# VC LMS - Complete Learning Management System with Version Control

## 🚀 Project Overview
VC LMS (Version Control Learning Management System) is a full-stack application combining file versioning with an intuitive admin-student interface. It enables universities to manage file uploads with version history tracking, role-based access, and a modern, minimal UI.

---

## 🎯 Problem Statement
Traditional LMS systems lack:
- Proper file versioning capabilities
- Clear distinction between admin and student workflows
- Intuitive interfaces for managing multiple student submissions
- Recent activity tracking for administrators

---

## ✅ Solution
VC LMS provides:
- **Dual-role system**: Separate workflows for Admin and Student
- **File Versioning**: Each upload creates a new version (v1, v2, v3...)
- **Admin Dashboard**: Search students, view files, track recent uploads
- **Student Portal**: Upload files with comments, download versions
- **JWT Authentication**: Secure role-based access control
- **Minimal UI Design**: Clean, professional black-white interface (Apple/Notion style)
- **Version History**: Preserve and access all previous file versions

---

## ⚙️ Key Features

### 👨‍💼 Admin Features
- 🔐 Secure login with username/password
- 🔍 Search students by name or URN
- 📊 Dashboard view of student files
- 📈 Recent file uploads section with refresh button
- 💾 Download any version of any student's file
- 📝 View file comments and metadata

### 👨‍🎓 Student Features
- 🔐 Login with name and URN
- 📤 Upload files with optional comments
- 📚 View all uploaded files and versions
- ⬇️ Download latest file versions
- 🕒 Track upload timestamps and version history
- 💬 Add comments to file uploads

### 🔧 System Features
- 🔄 Automatic versioning system
- 🛡️ JWT token-based authentication
- 📅 Timestamp tracking for all uploads
- 🗂️ Organized file storage by student URN
- 🎨 Responsive minimal UI design
- ⚡ Fast API backend with SQLAlchemy ORM

---

## 🛠 Tech Stack

### Frontend
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **HTTP Client**: Axios with JWT interceptors
- **Styling**: CSS3 with CSS variables
- **Design**: Minimal black-white theme (no gradients, no glows)

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with HS256
- **Server**: Uvicorn
- **File Handling**: FastAPI FileResponse for downloads

### DevOps
- **Frontend Port**: 5173 (Vite dev server)
- **Backend Port**: 8000 (Uvicorn)
- **Database**: SQLite (file-based)

---

## 📁 Project Structure
```
VC_Lms/
│
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # Database connection & session
│   ├── models.py               # SQLAlchemy models (File, Student)
│   ├── init_db.py              # Database initialization
│   ├── API_DOCUMENTATION.md    # API endpoint docs
│   └── routes/
│       ├── auth.py             # Admin login, student login
│       └── files.py            # Upload, download, search endpoints
│
├── frontend/
│   ├── src/
│   │   ├── App.vue             # Main app (role selection)
│   │   ├── style.css           # Global styles (minimal theme)
│   │   ├── services/
│   │   │   └── api.js          # Axios instance with JWT interceptor
│   │   ├── views/
│   │   │   ├── AdminLogin.vue  # Admin login (650px card)
│   │   │   ├── AdminDashboard.vue  # Search + recent uploads
│   │   │   ├── StudentLogin.vue    # Student login (name + URN)
│   │   │   └── StudentDashboard.vue # File upload & version history
│   │   └── components/
│   │       ├── StudentFilesModal.vue
│   │       └── Toast.vue       # Notifications
│   ├── package.json
│   └── vite.config.js
│
├── uploads/                    # File storage
├── QUICK_START.md             # Quick setup guide
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- SQLite

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python init_db.py
python main.py
```
Backend runs on `http://localhost:8000`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

---

## 📋 API Endpoints

### Authentication
- `POST /auth/admin/login` - Admin login (username, password)
- `POST /auth/student/login` - Student login (name, URN)
- `GET /auth/verify` - Verify JWT token

### Student Endpoints
- `POST /files/upload` - Upload file with comment
- `GET /files/my` - Get all student's files with versions
- `GET /files/my/latest` - Download latest file version

### Admin Endpoints
- `GET /files/admin/search` - Search students by name/URN
- `GET /files/admin/files` - Get files for specific student
- `GET /files/admin/download` - Download specific file version
- `GET /files/admin/recent` - Get recent 10 uploads across all students

---

## 🎨 UI Design

### Color Scheme (Minimal Black-White)
- **Background**: #000000
- **Cards**: #111111
- **Border**: #222222
- **Text Primary**: #ffffff
- **Text Secondary**: #aaaaaa
- **Accent**: #ffffff (no neon/glow effects)

### Key UI Components
- **Login Cards**: 650px wide, centered, simple borders
- **Admin Dashboard**: Search inputs + recent uploads section + search results table
- **Student Dashboard**: Upload section + file list with version history
- **Modals**: Clean borders, no shadows
- **Toast Notifications**: Simple text-based alerts

---

## 🔐 Authentication Flow

1. User selects role (Admin or Student)
2. **Admin**: Enters username & password
   - Backend verifies credentials
   - Returns JWT token
   - Redirects to Admin Dashboard
3. **Student**: Enters name & URN
   - Backend verifies student exists
   - Returns JWT token with student info
   - Redirects to Student Dashboard
4. Token stored in localStorage
5. All API requests include `Authorization: Bearer {token}` header

---

## 📊 File Versioning System

Each upload creates a new version:
```
Example: document.pdf
├── v1: document.pdf_v1 (uploaded Dec 1)
├── v2: document.pdf_v2 (uploaded Dec 5)
└── v3: document.pdf_v3 (uploaded Dec 10)
```

Metadata stored in database:
- Filename
- Version number
- Student URN
- Comment
- Upload timestamp
- File path

---

## 🌳 Directory Organization

Files are organized by student:
```
uploads/
├── S12345_document.pdf_v1
├── S12345_document.pdf_v2
├── S12345_slides.pptx_v1
├── S67890_report.docx_v1
└── ...
```

---

## 📝 Usage Examples

### Admin Workflow
1. Login with admin credentials
2. Search for student by name or URN
3. Click "View Files" to see student's files
4. Click "Download" to get latest version
5. Check "Recent File Uploads" section for activity

### Student Workflow
1. Login with name and URN
2. Click "Choose File" to select file
3. Add optional comment (e.g., "Final submission")
4. Click "Upload"
5. View all versions in "Your Files" section
6. Download latest version anytime

---

## 🔄 Database Schema

### File Model
```
- id: Primary key
- filename: Original filename
- filepath: Path to stored file
- version: Version number (auto-incrementing)
- student_name: Student's full name
- student_urn: Unique Reference Number
- comment: Upload comment
- uploaded_at: Timestamp
```

---

## 🛡️ Security Features
- **JWT Authentication**: Tokens expire and refresh
- **Role-Based Access**: Separate permissions for admin/student
- **Authorization Header**: All requests must include valid token
- **File Path Validation**: Prevents directory traversal attacks
- **CORS Disabled**: Only same-origin requests accepted

---

## 🐛 Troubleshooting

**Issue**: Frontend can't connect to backend
- Check backend is running on `localhost:8000`
- Check CORS settings in API config

**Issue**: Login fails
- Verify database is initialized: `python init_db.py`
- Check student/admin credentials exist in database

**Issue**: Files won't download
- Check `uploads/` directory exists
- Verify file path in database matches actual file
- Check user has permission to access file

---

## 📚 Additional Resources
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed endpoint info
- See [QUICK_START.md](QUICK_START.md) for setup guide
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing procedures

---

## 👥 Contributors
Manjot Singh,Manveer singh bhalla,Mannat kappor,Manas,mehak 

## 📄 License
MIT License

---

## ✨ Future Enhancements
- Role management system
- Bulk file operations
- Advanced search filters
- Email notifications
- Archive/delete functionality
- Analytics dashboard
