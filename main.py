from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
SECRET_KEY = "doomtracker-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
DATABASE_URL = "mysql+pymysql://root:@localhost/doomtracker"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────
class TransactionDB(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    title = Column(String(255))
    category = Column(String(255))
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    password = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────
class TransactionCreate(BaseModel):
    title: str
    category: str
    amount: float

class TransactionUpdate(BaseModel):
    title: str
    category: str
    amount: float

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class SpendingInput(BaseModel):
    income: float
    expense: float
    savings: float
    debt: float

# ─────────────────────────────────────────
# PASSWORD & JWT
# ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

bearer_scheme = HTTPBearer()

def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau expired. Silakan login ulang.",
        )

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    return user

# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "Backend jalan 🚀"}

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    new_user = UserDB(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Register success 🚀"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.email == user.email).first()

    if not existing:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if not verify_password(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_token(existing.id, existing.email)

    return {
        "message": "Login success 🚀",
        "token": token,
        "id": existing.id,
        "name": existing.name,
        "email": existing.email,
    }

# ─────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────
@app.get("/transactions")
def get_transactions(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(TransactionDB).filter(
        TransactionDB.user_id == current_user.id
    ).all()

@app.post("/transactions")
def create_transaction(
    transaction: TransactionCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_transaction = TransactionDB(
        user_id=current_user.id,
        title=transaction.title,
        category=transaction.category,
        amount=transaction.amount,
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return {"message": "Transaction added 🚀", "id": new_transaction.id}

@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(TransactionDB).filter(
        TransactionDB.id == transaction_id,
        TransactionDB.user_id == current_user.id,
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

    existing.title = transaction.title
    existing.category = transaction.category
    existing.amount = transaction.amount
    db.commit()
    db.refresh(existing)
    return {"message": "Transaction updated 🚀"}

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(TransactionDB).filter(
        TransactionDB.id == transaction_id,
        TransactionDB.user_id == current_user.id,
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

    db.delete(existing)
    db.commit()
    return {"message": "Transaction deleted 🚀"}

# ─────────────────────────────────────────
# AI PREDICT
# ─────────────────────────────────────────
@app.post("/predict")
def predict(data: SpendingInput):
    score = min(100, max(1, int(data.expense / 10)))

    if score < 30:
        result = "😎 Safe Spending"
    elif score < 70:
        result = "⚠️ Warning Spending"
    else:
        result = "💀 Doom Spending"

    return {"score": score, "result": result}