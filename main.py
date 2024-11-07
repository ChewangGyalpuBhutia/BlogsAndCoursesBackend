from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import shutil
import stripe

DATABASE_URL = "postgresql://postgres:9281@localhost/EduPvtLtd"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Set up CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    publish_time = Column(DateTime)
    image_path = Column(String)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    discount = Column(Float)

Base.metadata.create_all(bind=engine)

# Mount the images directory to serve static files
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/api/blog")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    publish_time: str = Form(...),
    image: UploadFile = File(...)
):
    db = SessionLocal()
    publish_time_dt = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M")
    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image.filename)
    absolute_image_path = os.path.abspath(image_path)
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    blog_post = BlogPost(title=title, content=content, publish_time=publish_time_dt, image_path=image_path)
    db.add(blog_post)
    db.commit()
    db.refresh(blog_post)
    return {"message": "Blog post scheduled successfully", "blog_post": blog_post}

@app.get("/api/blog")
def read_blog_posts():
    db = SessionLocal()
    blog_posts = db.query(BlogPost).all()
    return blog_posts

@app.post("/api/courses")
async def create_course(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    discount: float = Form(...),
    image: UploadFile = File(...)
):
    db = SessionLocal()
    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image.filename)
    absolute_image_path = os.path.abspath(image_path)
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    course = Course(name=name, description=description, price=price, discount=discount, image_path=image_path)
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"message": "Course created successfully", "course": course}

@app.get("/api/courses")
def read_courses():
    db = SessionLocal()
    courses = db.query(Course).all()
    return courses

stripe.api_key = "sk_test_51Q13P7Jy2Tche9ru9kAxFB7PBqJzbSoFCdtcoLTEsIEHoAXdn0gUthLBQPC9WPJH7oa5UWNrrXWYfmHQvri9fX7u00hn9zvjT1"

@app.post("/create-checkout-session/")
async def create_checkout_session(request: Request):
    try:
        body = await request.json()
        username = body.get("username")
        course_id = body.get("courseId")
        
        if not username or not course_id:
            raise HTTPException(status_code=400, detail="Username and courseId are required")
        
        # Create a product and price if not already created
        product = stripe.Product.create(name="Sample Product")
        price = stripe.Price.create(
            unit_amount=700,
            currency="usd",
            recurring={"interval": "month"},
            product=product.id,
        )
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price.id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:3000/',
            cancel_url='http://localhost:3000/',
        )
    
        return {"id": session.id, "message": "Redirecting to checkout page..."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")