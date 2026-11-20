import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://39egvB4SQKGLZwy.root:6wYkMwxKo9k4mlVA@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/test?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
