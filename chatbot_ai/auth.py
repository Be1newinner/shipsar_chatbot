import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from db import users_collection
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId  # Import this

load_dotenv()

security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

# Hash password before storing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Verify hashed password
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Generate JWT Token
def generate_token(user_id: str) -> str:
    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Register user
def register_user(username: str, email: str, password: str):
    if users_collection.find_one({"email": email}):
        return {"error": "Email already registered"}
    
    hashed_pw = hash_password(password)
    user_data = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}


# Login User
def login_user(email: str, password: str):
    user = users_collection.find_one({"email": email})
    
    if not user or not verify_password(password, user["password"]):
        return {"error": "Invalid credentials"}

    token = generate_token(str(user["_id"]))
    return {"message": "Login successful", "token": token}

# Decode JWT token
def decode_token(token: str):
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Get the current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # print("GET CURRENT USER => ",token)
    payload = decode_token(token)
    print("payload", payload)
    user = users_collection.find_one({"_id": ObjectId(payload["user_id"])})
    print(user)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user