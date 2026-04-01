from contextlib import asynccontextmanager
import importlib.util, sys, os

def load(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_base = os.path.dirname(__file__)

db           = load("src.database",        os.path.join(_base, "database.py"))
models       = load("src.models",          os.path.join(_base, "models.py"))
employees    = load("src.employees",       os.path.join(_base, "employees.py"))
shoutouts    = load("src.shoutouts",       os.path.join(_base, "shoutouts.py"))
achievements = load("src.achievements",    os.path.join(_base, "achievements.py"))
comments     = load("src.comments",        os.path.join(_base, "comments.py"))

engine       = db.engine
Base         = db.Base
SessionLocal = db.SessionLocal
Employee     = models.Employee

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.shoutouts.controller import router as shoutout_router
from src.api import router
from src.admin.controller import router as admin_router

def seed_employees():
    sess = SessionLocal()
    try:
        if sess.query(Employee).count() == 0:
            sess.add_all([
                Employee(name="Rahul",  department="Engineering"),
                Employee(name="Aman",   department="AI"),
                Employee(name="Satyam", department="Backend"),
                Employee(name="Priya",  department="Design"),
            ])
            sess.commit()
            print("[Seed] Employees seeded successfully")
        else:
            print("[Seed] Employees already exist, skipping")
    except Exception as e:
        sess.rollback()
        print(f"[Seed Error] {e}")
    finally:
        sess.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    import src.models
    import src.employees
    import src.shoutouts
    import src.achievements
    import src.comments

    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("[DB] Base tables ready")
    except Exception as e:
        print(f"[DB Init Warning] Base: {e} - continuing...")

    try:
        seed_employees()
    except Exception as e:
        print(f"[Seed Warning] {e} - continuing...")

    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shoutout_router)
app.include_router(router)
app.include_router(admin_router)
app.include_router(achievements.router)
app.include_router(shoutouts.router)
app.include_router(employees.router)
app.include_router(comments.router)

@app.get("/")
def root():
    return {"message": "BragBoard API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}