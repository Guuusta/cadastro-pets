"""API de Cadastro de Pets: as rotas do CRUD."""
from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

VERSAO = "0.1.0"

# Cria a tabela "pets" se ela ainda não existir
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cadastro de Pets - API", version=VERSAO)


def buscar_pet(pet_id: int, db: Session) -> models.Pet:
    """Busca um pet pelo id ou responde 404 (não encontrado)."""
    pet = db.get(models.Pet, pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    return pet


# ---------- Saúde ----------
@app.get("/health", tags=["saúde"])
def health():
    return {"status": "ok", "versao": VERSAO}


# ---------- C: criar ----------
@app.post("/pets", response_model=schemas.PetOut, status_code=status.HTTP_201_CREATED, tags=["pets"])
def criar_pet(dados: schemas.PetCreate, db: Session = Depends(get_db)):
    pet = models.Pet(**dados.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)          # pega o id que o banco gerou
    return pet


# ---------- R: listar todos ----------
@app.get("/pets", response_model=list[schemas.PetOut], tags=["pets"])
def listar_pets(db: Session = Depends(get_db)):
    return db.scalars(select(models.Pet).order_by(models.Pet.id)).all()


# ---------- R: ver um ----------
@app.get("/pets/{pet_id}", response_model=schemas.PetOut, tags=["pets"])
def ver_pet(pet_id: int, db: Session = Depends(get_db)):
    return buscar_pet(pet_id, db)


# ---------- U: atualizar ----------
@app.put("/pets/{pet_id}", response_model=schemas.PetOut, tags=["pets"])
def atualizar_pet(pet_id: int, dados: schemas.PetCreate, db: Session = Depends(get_db)):
    pet = buscar_pet(pet_id, db)
    for campo, valor in dados.model_dump().items():
        setattr(pet, campo, valor)
    db.commit()
    db.refresh(pet)
    return pet


# ---------- D: apagar ----------
@app.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["pets"])
def apagar_pet(pet_id: int, db: Session = Depends(get_db)):
    pet = buscar_pet(pet_id, db)
    db.delete(pet)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
