import os
import sys
from dotenv import load_dotenv

# Handle PyInstaller's extracted temp folder path
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(application_path, '.env')
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

APP_NAME = "Mobile Shop Inventory Manager"
APP_VERSION = "1.0.0"
