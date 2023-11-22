from sqlalchemy.orm import Session
import database, models, schemas
import passlib.hash as _hash
import jwt
import datetime as _dt
import email_validator as _evalid
from fastapi import HTTPException, Depends, security

oauth2schema = security.OAuth2PasswordBearer(tokenUrl="/api/token")

JWT_SECRET = "myjwtsecret"

async def get_user_by_email(email: str, db: Session):
    return db.query(models.User).filter(models.User.email == email).first()

async def create_user(user: schemas.UserCreate, db: Session):
    try:
        valid = _evalid.validate_email(email=user.email)

        email = valid.email
    except _evalid.EmailNotValidError:
        raise HTTPException(status_code=404, detail="Please enter a valid email")

    hashed_password = _hash.bcrypt.hash(user.hashed_password)     

    user_obj = models.User(
        email=email, hashed_password=hashed_password 
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

async def authenticate_user(email: str, password: str, db: Session):
    user = await get_user_by_email(db=db, email=email)

    if not user:
        return False

    if not user.verify_password(password):
        return False

    return user

async def create_token(user: models.User):

    user_schema_obj = schemas.User.from_orm(user)
    user_dict = user_schema_obj.dict()    
    token = jwt.encode(user_dict, JWT_SECRET)
    return dict(access_token=token, token_type="bearer")

async def get_current_user(
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2schema)
):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(models.User).get(payload["id"])
    except:
        raise HTTPException(status_code=401, details="Invalid Email or Password")
    return schemas.User.from_orm(user)

async def create_lead(user: schemas.User, db: Session, lead: schemas.LeadCreate):
    lead = models.Lead(**lead.dict(), owner_id=user.id)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return schemas.Lead.from_orm(lead)

async def get_leads(user: schemas.User, db: Session):
    leads = db.query(models.Lead).filter_by(owner_id=user.id)

    return list(map(schemas.Lead.from_orm, leads)
)

async def lead_selector(lead_id: int, user: schemas.User, db: Session):
    lead = (
        db.query(models.Lead)
        .filter_by(owner_id=user.id)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if lead is None:
        raise HTTPException(status_code=404, detail="Lead does not exist")

    return lead

async def get_lead(lead_id: int, user: schemas.User, db: Session):
    lead = await lead_selector(lead_id=lead_id, user=user, db=db)

    return schemas.Lead.from_orm(lead)

async def delete_lead(lead_id: int, user: schemas.User, db: Session):
    lead = await lead_selector(lead_id, user, db)

    db.delete(lead)
    db.commit()   

async def update_lead(lead_id: int, lead: schemas.LeadCreate, user: schemas.User, db: Session):
    lead_db = await lead_selector(lead_id, user, db)

    lead_db.first_name = lead.first_name  
    lead_db.last_name = lead.last_name
    lead_db.email = lead.email
    lead_db.company = lead.company
    lead_db.note = lead.note
    lead_db.date_last_updated = _dt.datetime.utcnow()

    db.commit()
    db.refresh(lead_db)

    return schemas.Lead.from_orm(lead_db)
