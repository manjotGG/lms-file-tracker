from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException, status, Header
from fastapi.responses import FileResponse
import shutil
import os
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from collections import defaultdict
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

UPLOAD_DIR = "uploads"
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_auth_header(authorization: str = Header(None)):
    """Extract and verify authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )


# Student endpoints
@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    comment: str = Query(""),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Upload file - Student only"""
    user = get_auth_header(authorization)
    
    if user["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload files"
        )
    
    student_name = user["student_name"]
    student_urn = user["student_urn"]
    
    # Get next version number
    existing = db.query(models.File).filter(
        models.File.filename == file.filename,
        models.File.student_urn == student_urn
    ).all()
    version = len(existing) + 1

    # Create file path
    file_path = f"{UPLOAD_DIR}/{student_urn}_{file.filename}_v{version}"

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Record in database
    new_file = models.File(
        filename=file.filename,
        version=version,
        filepath=file_path,
        student_name=student_name,
        student_urn=student_urn,
        comment=comment
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {
        "success": True,
        "filename": file.filename,
        "version": version,
        "student_urn": student_urn,
        "comment": comment,
        "uploaded_at": new_file.uploaded_at
    }


@router.get("/my")
def get_my_files(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get all files for current student"""
    user = get_auth_header(authorization)
    
    if user["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student_urn = user["student_urn"]
    
    files = db.query(models.File).filter(
        models.File.student_urn == student_urn
    ).all()
    
    if not files:
        return {
            "student_urn": student_urn,
            "files": []
        }
    
    # Group by filename
    files_dict = defaultdict(list)
    for f in files:
        files_dict[f.filename].append({
            "id": f.id,
            "version": f.version,
            "comment": f.comment,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        })
    
    # Sort versions
    for filename in files_dict:
        files_dict[filename].sort(key=lambda x: x["version"], reverse=True)
    
    return {
        "student_urn": student_urn,
        "files": [{"filename": fn, "versions": v} for fn, v in files_dict.items()]
    }


@router.get("/my/latest")
def download_my_latest(
    filename: str = Query(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Download latest version of student's file"""
    user = get_auth_header(authorization)
    
    if user["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can download their files"
        )
    
    student_urn = user["student_urn"]
    
    # Get latest file
    file_record = db.query(models.File).filter(
        models.File.filename == filename,
        models.File.student_urn == student_urn
    ).order_by(models.File.version.desc()).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_record.filepath,
        filename=f"{filename}_v{file_record.version}"
    )


# Admin endpoints
@router.get("/admin/search")
def admin_search(
    student_name: str = Query(None),
    student_urn: str = Query(None),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Admin search for students"""
    user = get_auth_header(authorization)
    
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can search"
        )
    
    if not student_name and not student_urn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide student_name or student_urn"
        )
    
    query = db.query(models.File)
    
    if student_name:
        student_name = student_name.strip().lower()
        query = query.filter(models.File.student_name == student_name)
    
    if student_urn:
        query = query.filter(models.File.student_urn == student_urn)
    
    files = query.all()
    
    if not files:
        return {"students": []}
    
    # Group by student
    students_dict = {}
    for f in files:
        key = (f.student_name, f.student_urn)
        if key not in students_dict:
            students_dict[key] = []
        students_dict[key].append(f)
    
    students = [
        {
            "student_name": name,
            "student_urn": urn,
            "file_count": len(files_list)
        }
        for (name, urn), files_list in students_dict.items()
    ]
    
    return {"students": students}


@router.get("/admin/files")
def admin_get_files(
    student_urn: str = Query(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Admin get all files for a student"""
    user = get_auth_header(authorization)
    
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint"
        )
    
    files = db.query(models.File).filter(
        models.File.student_urn == student_urn
    ).all()
    
    if not files:
        return {
            "student_urn": student_urn,
            "files": []
        }
    
    student = files[0]
    
    # Group by filename
    files_dict = defaultdict(list)
    for f in files:
        files_dict[f.filename].append({
            "id": f.id,
            "version": f.version,
            "comment": f.comment,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        })
    
    # Sort versions
    for filename in files_dict:
        files_dict[filename].sort(key=lambda x: x["version"], reverse=True)
    
    return {
        "student_name": student.student_name,
        "student_urn": student.student_urn,
        "files": [{"filename": fn, "versions": v} for fn, v in files_dict.items()]
    }


@router.get("/admin/download")
def admin_download(
    student_urn: str = Query(...),
    filename: str = Query(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Admin download latest file version"""
    user = get_auth_header(authorization)
    
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can download files"
        )
    
    file_record = db.query(models.File).filter(
        models.File.filename == filename,
        models.File.student_urn == student_urn
    ).order_by(models.File.version.desc()).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(file_record.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_record.filepath,
        filename=f"{file_record.student_name}_{filename}_v{file_record.version}"
    )

    


@router.get("/download/latest/")
def download_latest_file(
    student_urn: str, 
    filename: str, 
    db: Session = Depends(get_db)
):
    """Download the latest version of a specific file"""
    file = db.query(models.File).filter(
        models.File.student_urn == student_urn,
        models.File.filename == filename
    ).order_by(models.File.version.desc()).first()

    if not file:
        return {"error": "File not found"}

    return FileResponse(path=file.filepath, filename=file.filename)


@router.get("/download/all-latest/")
def download_all_latest(student_urn: str, db: Session = Depends(get_db)):
    """Download all latest versions"""
    files = db.query(models.File).filter(
        models.File.student_urn == student_urn
    ).all()
    
    if not files:
        return {"error": "No files found"}
    
    latest_files = {}
    for f in files:
        if f.filename not in latest_files or f.version > latest_files[f.filename]["version"]:
            latest_files[f.filename] = {
                "version": f.version,
                "filepath": f.filepath,
                "filename": f.filename,
                "comment": f.comment,
                "uploaded_at": f.uploaded_at,
                "id": f.id
            }
    
    return {
        "student_urn": student_urn,
        "total_files": len(latest_files),
        "files": list(latest_files.values())
    }


@router.get("/download/{file_id}")
def download_file(file_id: int, db: Session = Depends(get_db)):
    """Download a specific file by ID"""
    file = db.query(models.File).filter(models.File.id == file_id).first()
    if not file:
        return {"error": "File not found"}
    return FileResponse(path=file.filepath, filename=file.filename)


@router.get("/admin/")
def admin_view(db: Session = Depends(get_db)):
    """Admin view of all students and files"""
    files = db.query(models.File).all()
    
    if not files:
        return {"error": "No files in database"}
    
    students_dict = defaultdict(lambda: {"student_urn": None, "files": {}})
    
    for f in files:
        student_key = f.student_name
        students_dict[student_key]["student_urn"] = f.student_urn
        
        if f.filename not in students_dict[student_key]["files"]:
            students_dict[student_key]["files"][f.filename] = []
        
        students_dict[student_key]["files"][f.filename].append({
            "version": f.version,
            "comment": f.comment,
            "uploaded_at": f.uploaded_at,
            "id": f.id
        })
    
    result = []
    for student_name, student_data in students_dict.items():
        files_list = []
        for filename, versions in student_data["files"].items():
            versions.sort(key=lambda x: x["version"])
            files_list.append({"filename": filename, "versions": versions})
        
        result.append({
            "student_name": student_name,
            "student_urn": student_data["student_urn"],
            "files": files_list
        })
    
    return {"total_students": len(result), "students": result}


@router.get("/admin/files/")
def admin_files(db: Session = Depends(get_db)):
    """List all files in database"""
    files = db.query(models.File).all()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "version": f.version,
            "student_name": f.student_name,
            "student_urn": f.student_urn,
            "comment": f.comment,
            "uploaded_at": f.uploaded_at
        }
        for f in files
    ]


@router.get("/admin/summary")
def summary(db: Session = Depends(get_db)):
    """Summary statistics"""
    files = db.query(models.File).all()
    data = {}
    for f in files:
        key = f.student_name
        data[key] = data.get(key, 0) + 1
    
    return {
        "total_records": len(files),
        "total_students": len(data),
        "students": data
    }
