from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://root:@localhost/doom_tracker"

engine = create_engine(DATABASE_URL)

connection = engine.connect()

print("MYSQL CONNECTED 🚀")