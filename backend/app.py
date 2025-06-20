from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel , EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import sqlite3
import requests
import bcrypt
import pandas as pd
import uvicorn
import os, httpx
from dotenv import load_dotenv
from scraper import scrape_by_keyword


load_dotenv()
BACKEND_SECRET_KEY        = os.getenv("BACKEND_SECRET_KEY", "changeme")
ALGORITHM                 = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10"))
METABASE_SITE_URL         = os.getenv("METABASE_SITE_URL", "http://localhost:3000")
METABASE_SECRET_KEY       = os.getenv("METABASE_SECRET_KEY")
OUTPUT_DIR                = "/Users/Cheokerinos/metabase_data"
DB_PATH                   = "users.db"
METABASE_USERNAME         = os.getenv("METABASE_USERNAME")
METABASE_PASSWORD         = os.getenv("METABASE_PASSWORD")
REFRESH_EXPIRE            = timedelta(days=7)
REFRESH_TOKEN_DB          = "refresh_tokens.db"


if not METABASE_SECRET_KEY:
    raise RuntimeError("METABASE_SECRET_KEY not set")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Setting up Database ---
DB_PATH = "users.db"
def init_user_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        hashed_password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    
def init_refresh_token_db():
    conn = sqlite3.connect(REFRESH_TOKEN_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_user_db()
init_refresh_token_db()

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "running", "message": "Power BI scraper back-end is up"}  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # if using Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email:    EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def check_strength(cls, pw: str):
        # require uppercase, lowercase, digit, special‐char
        import re
        if not re.search(r"[A-Z]",   pw): 
            raise ValueError("must contain an uppercase letter")
        if not re.search(r"[a-z]",   pw): 
            raise ValueError("must contain a lowercase letter")
        if not re.search(r"\d",      pw): 
            raise ValueError("must contain a digit")
        if not re.search(r"\W",      pw): 
            raise ValueError("must contain a special character")
        return pw

    
# --- Utilities ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_user(username: str) -> Optional[RegisterRequest]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
      "SELECT username, email, hashed_password FROM users WHERE username = ?",
      (username,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"username": row[0], "email": row[1], "password": row[2]}

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["password"]):
        return None
    return user


def create_access_token(
    payload: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, BACKEND_SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("Checking token:", token)
    creds_exc = HTTPException(
      status_code=401,
      detail="Invalid authentication",
      headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(token, BACKEND_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise creds_exc
    except JWTError:
        raise creds_exc
    user = get_user(username)
    if not user:
        raise creds_exc
    return user

def is_refresh_token_still_valid(username: str, token: str) -> bool:
    conn = sqlite3.connect(REFRESH_TOKEN_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM refresh_tokens
        WHERE username = ? AND token = ?
    """, (username, token))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def rotate_refresh_token(username: str, old: str, new: str):
    conn = sqlite3.connect(REFRESH_TOKEN_DB)
    cursor = conn.cursor()
    # Delete old token
    cursor.execute("""
        DELETE FROM refresh_tokens WHERE username = ? AND token = ?
    """, (username, old))
    
    # Insert new token
    cursor.execute("""
        INSERT INTO refresh_tokens (username, token, created_at)
        VALUES (?, ?, ?)
    """, (username, new, datetime.utcnow()))
    
    conn.commit()
    conn.close()
    
def save_refresh_token(username: str, token: str):
    conn = sqlite3.connect(REFRESH_TOKEN_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO refresh_tokens (username, token, created_at)
        VALUES (?, ?, ?)
    """, (username, token, datetime.utcnow()))
    conn.commit()
    conn.close()
    
# ---Email Validator---
ABSTRACT_KEY = os.getenv("ABSTRACT_API_KEY")
if not ABSTRACT_KEY:
    raise RuntimeError("ABSTRACT_API_KEY not set")

async def validate_email_with_abstract(email: str):
    url = "https://emailvalidation.abstractapi.com/v1/"
    params = {"api_key": ABSTRACT_KEY, "email": email}       
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
    if r.status_code != 200:
        raise HTTPException(502, "Email validation service unavailable")
    data = r.json()
    print("Validation result from AbstractAPI:", data)
    # you can inspect more fields; here are the key ones:
    if not data.get("is_valid_format", {}).get("value", False):
        raise HTTPException(400, "Email format is invalid")
    if not data.get("is_smtp_valid", {}).get("value", False):
        raise HTTPException(400, "Email domain does not accept mail")
    if data.get("is_disposable_email", {}).get("value", False):
        raise HTTPException(400, "Disposable emails are not allowed")
    # optionally check catch-all / role-based etc.
    return True

# ---Authentication End Points---
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, bg:BackgroundTasks):
    await validate_email_with_abstract(req.email)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
      "SELECT 1 FROM users WHERE username = ?",
      (req.username,)
    )
    if cur.fetchone():
        conn.close()
        raise HTTPException(400, "Username already exists")
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
      "INSERT INTO users (username,email,hashed_password) VALUES (?,?,?)",
      (req.username, req.email, hashed)
    )
    conn.commit()
    conn.close()
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(form: LoginRequest):
    user = authenticate_user(form.username, form.password)
    if not user:
       raise HTTPException(401, "Incorrect username or password")
    access_token = create_access_token(
        {"sub": user["username"], "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        {"sub": user["username"], "type": "refresh"},
        REFRESH_EXPIRE,
    )
    save_refresh_token(user["username"], refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/refresh_token")
def refresh_token(req: RefreshRequest):
    print("Incoming refresh:", req.refresh_token)
    try:
        payload = jwt.decode(req.refresh_token, BACKEND_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError()
        username = payload["sub"]
    except JWTError:
        print("Refresh token invalid or wrong type")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # optionally check against DB to see if this refresh token is still valid
    if not is_refresh_token_still_valid(username, req.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    # issue new pair
    new_access  = create_access_token({"sub": username, "type" : "access"}, timedelta(ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh = create_access_token({"sub": username, "type": "refresh"}, REFRESH_EXPIRE)

    # update DB record
    rotate_refresh_token(username, old=req.refresh_token, new=new_refresh)

    return Token(access_token=new_access, refresh_token=new_refresh, token_type="bearer")


'''
@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code = 400, detail = "Only CSV files are allowed.")
    csv_bytes = await file.read()
    dataset_name = os.path.splitext(file.filename)[0]
    try:
        response = await import_csv_to_powerbi(csv_bytes, dataset_name)
        report_id = response["import"]["reports"][0]["id"]
        embed_token = await generate_embed_token(report_id)
        embed_url = response["import"]["reports"][0]["id"]
        return JSONResponse(content = {"filename": file.filename})
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
'''

class EmbedRequest(BaseModel):
    dashboard_id: int
    # Optionally, you can pass params to filter the dashboard:
    params: Optional[dict] = {}
    
class EmbedTableRequest(BaseModel):
    question_id: int
    # Optionally, you can pass params to filter the dashboard:
    params: Optional[dict] = {}

class EmbedResponse(BaseModel):
    iframe_url: str

@app.get("/dashboards")
async def list_dashboards(current_user: dict = Depends(get_current_user)):
    session_resp = requests.post(
        f"{METABASE_SITE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
    )
    if session_resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to authenticate with Metabase")

    session_token = session_resp.json()["id"]

    resp = requests.get(
        f"{METABASE_SITE_URL}/api/dashboard",
        headers={"X-Metabase-Session": session_token}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to get dashboards")
    data = resp.json()
    embedded_dashboards = [
        {"id": d["id"], "name": d["name"]}
        for d in data
        if d.get("enable_embedding") is True
    ]
    return embedded_dashboards

@app.post("/embed", response_model=EmbedResponse)
async def get_embed_url(
    req: EmbedRequest,
    current_user: dict = Depends(get_current_user),
):
    # Build Metabase embed JWT
    # payload must include resource and optional params, and exp
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
    payload = {
        "resource": {"dashboard": req.dashboard_id},
        "params": req.params or {},
        "exp": int(expire.timestamp()),
    }
    metabase_token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
    # Build iframe URL
    # #bordered=true&titled=true are optional UI flags
    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{metabase_token}#bordered=true&titled=true"
    return {"iframe_url": iframe_url}

@app.get("/tables")
async def list_tables(current_user: dict = Depends(get_current_user)):
    session_resp = requests.post(
        f"{METABASE_SITE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
    )
    if session_resp.status_code != 200:
        raise HTTPException(502, "Failed to authenticate with Metabase")

    session_token = session_resp.json()["id"]

    resp = requests.get(
        f"{METABASE_SITE_URL}/api/card",
        headers={"X-Metabase-Session": session_token}
    )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, "Failed to get card list")

    data = resp.json()

    embedded_cards = [
        {"id": c["id"], "name": c["name"]}
        for c in data
        if c.get("enable_embedding") is True
    ]
    return embedded_cards

@app.post("/embed_table", response_model=EmbedResponse)
async def get_table_embed_url(
    req: EmbedTableRequest,
    current_user: dict = Depends(get_current_user),
):
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=5)
    payload = {
        "resource": {"question": req.question_id},
        "params": req.params or {},
        "exp": int(expire.timestamp()),
    }
    metabase_token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    iframe_url = f"{METABASE_SITE_URL}/embed/question/{metabase_token}#bordered=true&titled=true"
    return {"iframe_url": iframe_url}

    

#---Tender Scraper--
class KeywordRequest(BaseModel):
    keywords: List[str]


OUTPUT_DIR = "/Users/Cheokerinos/metabase_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

    
@app.post("/generate")
def scrape_tenders(request: KeywordRequest,
                   current_user: dict = Depends(get_current_user)):
    all_results = []
    for keyword in request.keywords:
        print(f"Scraping for keyword: {keyword}")
        results = scrape_by_keyword(keyword)
        if results:
            for result in results:
                if result not in all_results:
                    all_results.append(result)
    for result in all_results:
        respondents = result.get("Respondents")
        if isinstance(respondents, list):
            formatted = [f"{r} - {a}" for r, a in respondents]
            result["Respondents"] = " | ".join(formatted)
            result["No. of Respondents"] = len(respondents)
        else:
            result["Respondents"] = "N/A"
            result["No. of Respondents"] = 0
    df = pd.DataFrame(all_results)
    sort_order = ["OPEN","AWARDED","PENDING AWARD","NO AWARD"]
    df['Awarded'] = pd.Categorical(df['Awarded'], categories=sort_order, ordered=True)
    df.sort_values(by=['Awarded', 'Title'], inplace=True)  # Sort by Tab and then Title
    df.insert(0, 'S/N', range(1, len(df)+1))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/tenders_{timestamp}.csv"
    csv_path = f"{OUTPUT_DIR}/tenders_{timestamp}.csv"
    sqlite_path = f"{OUTPUT_DIR}/mydata.db"
    df.to_csv(filename, index=False)
    csv_to_sqlite(csv_path,sqlite_path)
    
    
    return {
        "message": f"{len(all_results)} records saved.",
        "csv_path": filename,
        "results": all_results}
    

    
def csv_to_sqlite(csv_path, sqlite_path, table_name="tenders"):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)