from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://root:@localhost/doomtracker"

engine = create_engine(DATABASE_URL)

connection = engine.connect()

print("MYSQL CONNECTED 🚀")