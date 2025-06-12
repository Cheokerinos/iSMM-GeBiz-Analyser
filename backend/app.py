from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel , EmailStr, constr, validator
from typing import List, Optional
from datetime import datetime, timedelta
import sqlite3
import bcrypt
import pandas as pd
import uvicorn
import os
from dotenv import load_dotenv
from scraper import scrape_by_keyword


load_dotenv()
BACKEND_SECRET_KEY        = os.getenv("BACKEND_SECRET_KEY", "changeme")
ALGORITHM                 = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
METABASE_SITE_URL         = os.getenv("METABASE_SITE_URL", "http://localhost:3000")
METABASE_SECRET_KEY       = os.getenv("METABASE_SECRET_KEY")
OUTPUT_DIR                = "/Users/Cheokerinos/metabase_data"
DB_PATH                   = "users.db"

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

init_user_db()

# --- Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: constr = constr(min_length=8)
    
    @validator("password")
    def password_strength(cls, pw: str):
        import re
        pattern = re.compile(
          r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).+$"
        )
        if not pattern.match(pw):
            raise ValueError(
              "Password must: 1 uppercase, 1 lowercase, 1 digit & 1 special char"
            )
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


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": sub}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, BACKEND_SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
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

# ---Authentication End Points---
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    if get_user(req.username):
        raise HTTPException(400, "Username already exists")
    hashed = hash_password(req.password)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
      "INSERT INTO users (username,email,hashed_password) VALUES (?,?,?)",
      (req.username, req.email, hashed)
    )
    conn.commit(); conn.close()
    return {"message":"User registered"}

@app.post("/login", response_model=Token)
def login(form: LoginRequest):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

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

class EmbedRequest(BaseModel):
    dashboard_id: int
    # Optionally, you can pass params to filter the dashboard:
    params: Optional[dict] = {}

class EmbedResponse(BaseModel):
    iframe_url: str

@app.post("/embed", response_model=EmbedResponse)
async def get_embed_url(
    req: EmbedRequest,
    current_user: User = Depends(get_current_user),
):
    # Build Metabase embed JWT
    # payload must include resource and optional params, and exp
    payload = {
        "resource": {"dashboard": req.dashboard_id},
        "params": req.params or {},
        "exp": int((datetime.utcnow() + timedelta(minutes=10)).timestamp()),
    }
    metabase_token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
    # Build iframe URL
    # #bordered=true&titled=true are optional UI flags
    iframe_url = f"{METABASE_SITE_URL}/embed/dashboard/{metabase_token}#bordered=true&titled=true"
    return {"iframe_url": iframe_url}
'''

#---Tender Scraper--
class KeywordRequest(BaseModel):
    keywords: List[str]


OUTPUT_DIR = "/Users/Cheokerinos/metabase_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

    
@app.post("/generate")
def scrape_tenders(request: KeywordRequest):
    all_results = []
    for keyword in request.keywords:
        print(f"Scraping for keyword: {keyword}")
        results = scrape_by_keyword(keyword)
        if results:
            for result in results:
                if result not in all_results:
                    all_results.append(result)
    
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