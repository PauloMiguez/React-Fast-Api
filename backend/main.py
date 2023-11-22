from fastapi import FastAPI, Depends, HTTPException, security
from sqlalchemy.orm import Session
from database import create_db, get_db
import schemas, services
from typing import List
from fastapi.middleware.cors import CORSMiddleware

create_db()

app = FastAPI()

origins = [
    'http://localhost:3000'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.post("/api/users/")
async def create_user(
    user: schemas.UserCreate, db: Session = Depends(get_db)
):
    db_user = await services.get_user_by_email(email=user.email, db=db)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    user = await services.create_user(user=user, db=db)

    return await services.create_token(user)


@app.post("/api/token")
async def generate_token(
    form_data: security.OAuth2PasswordRequestForm = Depends(), 
    db: Session= Depends(get_db)
):
    user = await services.authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    return await services.create_token(user)    

@app.get("/api/users/me", response_model=schemas.User)
async def get_user(user: schemas.User = Depends(services.get_current_user)):
    return user 

@app.post("/api/leads/", response_model=schemas.Lead)
async def create_lead(
    lead: schemas.LeadCreate, 
    user: schemas.User=Depends(services.get_current_user), 
    db: Session = Depends(get_db),
):
    return await services.create_lead(user=user,db=db, lead=lead)

@app.get("/api/leads/", response_model=List[schemas.Lead])
async def get_leads(
    user: schemas.User=Depends(services.get_current_user), 
    db: Session = Depends(get_db),
):
    return await services.get_leads(user=user, db=db)

@app.get("/api/leads/{lead_id}", status_code=200)
async def get_lead(lead_id: int, user: schemas.User = Depends(services.get_current_user),
    db: Session = Depends(get_db),
):
    return await services.get_lead(lead_id, user, db)

@app.delete("/api/leads/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: int, 
    user: schemas.User = Depends(services.get_current_user),
    db: Session = Depends(get_db),
):
    await services.delete_lead(lead_id, user, db)
    return {"message", "Successfully Deleted"}

@app.put("/api/leads/{lead_id}", status_code=200)
async def update_lead(
    lead_id: int, 
    lead: schemas.LeadCreate,
    user: schemas.User = Depends(services.get_current_user),
    db: Session = Depends(get_db),
):
    await services.update_lead(lead_id, lead, user, db)
    return {"message", "Successfully Updated"}

@app.get("/api/")
async def root():
    return {"message": "Awesome Leads Manager"}