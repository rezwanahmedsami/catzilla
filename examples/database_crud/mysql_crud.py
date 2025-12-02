import asyncio
from catzilla import Catzilla, service, Depends, Path, JSONResponse
from catzilla.dependency_injection import set_default_container
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# from database import SessionLocal
app = Catzilla(title="Student Management System", version="1.0.0")

set_default_container(app.di_container)

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    # date column int unix timestamp
    date = Column(Integer, nullable=False)


@service("database_config", scope="singleton")
class DatabaseConfig:
    """Database configuration service"""

    def __init__(self):
        # Using mysql database configuration from database.py
        self.MYSQL_USER = "root"
        self.MYSQL_PASSWORD = ""
        self.MYSQL_HOST = "localhost"
        self.MYSQL_PORT = 3306
        self.MYSQL_DB = "student_db"

        DATABASE_URL = (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

        self.engine = create_engine(DATABASE_URL, echo=False, future=True)
        self.db = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # def get_db(self):
        #     db = self.SessionLocal()
        #     try:
        #         yield db
        #     finally:
        #         db.close()

        print("📋 Database configuration initialized")

@service("student_service")
class StudentService:
    def __init__(self, db_config=Depends("database_config")):
        self.db_config = db_config

    def get_student(self, student_id: int):
        db = self.db_config.db()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return None
            return {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "date": student.date
            }
        finally:
            db.close()
    
    def get_all_students(self):
        db = self.db_config.db()
        try:
            students = db.query(Student).all()
            return [{
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "date": s.date
            } for s in students]
        finally:
            db.close()
    
    def create_student(self, name: str, email: str, date: int):
        db = self.db_config.db()
        try:
            student = Student(name=name, email=email, date=date)
            db.add(student)
            db.commit()
            db.refresh(student)
            return {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "date": student.date
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def update_student(self, student_id: int, name: str = None, email: str = None, date: int = None):
        db = self.db_config.db()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return None
            
            if name is not None:
                student.name = name
            if email is not None:
                student.email = email
            if date is not None:
                student.date = date
            
            db.commit()
            db.refresh(student)
            return {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "date": student.date
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def delete_student(self, student_id: int):
        db = self.db_config.db()
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return False
            
            db.delete(student)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
@app.get("/students")
async def list_students(request, student_service: StudentService = Depends("student_service")):
    students = student_service.get_all_students()
    return JSONResponse(students)

@app.get("/students/{student_id}")
async def read_student(request, student_id: int = Path(..., ge=1), student_service: StudentService = Depends("student_service")):
    student = student_service.get_student(student_id)
    if not student:
        return JSONResponse({"message": "Student not found"}, status_code=404)
    return JSONResponse(student)

@app.post("/students")
async def create_student(request, student_service: StudentService = Depends("student_service")):
    data = request.json()
    try:
        student = student_service.create_student(
            name=data.get("name"),
            email=data.get("email"),
            date=data.get("date")
        )
        return JSONResponse(student, status_code=201)
    except Exception as e:
        return JSONResponse({"message": f"Error creating student: {str(e)}"}, status_code=400)

@app.put("/students/{student_id}")
async def update_student(request, student_id: int = Path(..., ge=1), student_service: StudentService = Depends("student_service")):
    data = request.json()
    try:
        student = student_service.update_student(
            student_id=student_id,
            name=data.get("name"),
            email=data.get("email"),
            date=data.get("date")
        )
        if not student:
            return JSONResponse({"message": "Student not found"}, status_code=404)
        return JSONResponse(student)
    except Exception as e:
        return JSONResponse({"message": f"Error updating student: {str(e)}"}, status_code=400)

@app.delete("/students/{student_id}")
async def delete_student(request, student_id: int = Path(..., ge=1), student_service: StudentService = Depends("student_service")):
    try:
        success = student_service.delete_student(student_id)
        if not success:
            return JSONResponse({"message": "Student not found"}, status_code=404)
        return JSONResponse({"message": "Student deleted successfully"})
    except Exception as e:
        return JSONResponse({"message": f"Error deleting student: {str(e)}"}, status_code=400)


if __name__ == "__main__":
    print("API Endpoints:")
    print("  GET    /students          - List all students")
    print("  GET    /students/{id}     - Get student by ID")
    print("  POST   /students          - Create new student")
    print("  PUT    /students/{id}     - Update student")
    print("  DELETE /students/{id}     - Delete student")
    app.listen(port=3000)