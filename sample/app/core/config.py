import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "microlearning.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
TIMER_SECONDS = 420
APP_HOST = "0.0.0.0"
APP_PORT = 7860
COMPLIANCE_PAGE_SIZE = 10
