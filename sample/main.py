import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Request

from app.core.database import get_conn
from app.data.loader import load_compliance_data, seed_demo_data


def create_tables():
    import os as _os
    schema_path = _os.path.join(_os.path.dirname(__file__), "app", "data", "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        sql = f.read()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
        conn.commit()
        print("Tables created/verified")
    finally:
        conn.close()


def is_table_empty(table_name):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            return cur.fetchone()["cnt"] == 0
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    create_tables()
    if is_table_empty("comp_penalties"):
        print("Loading compliance data (first run)...")
        load_compliance_data()
    if is_table_empty("modules"):
        print("Seeding demo data...")
        seed_demo_data()
    print("Ready.")
    yield


app = FastAPI(lifespan=lifespan)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mount static files if directory exists
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import routers
from app.api.auth import router as auth_router
from app.api.modules import router as modules_router
from app.api.sprint import router as sprint_router
from app.api.quiz import router as quiz_router
from app.api.dashboard import router as dashboard_router
from app.api.compliance import router as compliance_router

app.include_router(auth_router, prefix="/api")
app.include_router(modules_router, prefix="/api")
app.include_router(sprint_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=False)
