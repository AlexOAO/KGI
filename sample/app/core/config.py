import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "kgi")
DB_PASSWORD = os.getenv("DB_PASSWORD", "kgi_pass")
DB_NAME = os.getenv("DB_NAME", "kgi_learning")
TIMER_SECONDS = int(os.getenv("TIMER_SECONDS", "420"))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
