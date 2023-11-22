import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm

DATABASE_URL = "sqlite:///./database.db"

engine = _sql.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = _declarative.declarative_base()

def create_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

       