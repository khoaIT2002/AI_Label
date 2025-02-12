from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from crud.role import gets_roles, creates_role, updates_role, deletes_role
from schemas.role import RoleInDB, RoleCreate, RoleUpdate
from core.database import get_db
router = APIRouter()
@router.get("/roles/", response_model=list[RoleInDB])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = gets_roles(db, skip=skip, limit=limit)
    return roles
@router.post("/roles/", response_model=RoleInDB)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return creates_role(db, role)

@router.put("/roles/{role_id}", response_model=RoleInDB)
def update_role(role_id: str, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = updates_role(db, role_id, role)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.delete("/roles/{role_id}", response_model=RoleInDB)
def delete_role(role_id: str, db: Session = Depends(get_db)):
    db_role = deletes_role(db, role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role