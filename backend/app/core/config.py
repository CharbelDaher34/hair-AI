import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 18000))

# Google OAuth settings (Removed)
# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# GOOGLE_REDIRECT_URI_HR = os.getenv("GOOGLE_REDIRECT_URI_HR", "http://84.16.230.94:8017/api/v1/auth/google/callback/hr")

# OAuth Scopes (Removed)
# GOOGLE_SCOPES = [
#     "https://www.googleapis.com/auth/userinfo.email",
#     "https://www.googleapis.com/auth/userinfo.profile",
#     "openid"
# ]
