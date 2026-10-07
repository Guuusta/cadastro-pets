"""API de Cadastro de Pets: as rotas do CRUD."""
import os

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

VERSAO = "0.3.0"

# Cria a tabela "pets" se ela ainda não existir
Base.metadata.create_all(bind=engine)

# ROOT_PATH: o "endereço base" quando a API está atrás de um proxy.
# Atrás do Nginx ela mora em /api, então a página /docs precisa saber disso
# para montar os links certos (/api/openapi.json). Sem proxy, fica vazio.
app = FastAPI(title="Cadastro de Pets - API", version=VERSAO, root_path=os.getenv("ROOT_PATH", ""))


def buscar_pet(pet_id: int, db: Session) -> models.Pet:
    """Busca um pet pelo id ou responde 404 (não encontrado)."""
    pet = db.get(models.Pet, pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    return pet


# ---------- Saúde ----------
# Não basta responder "estou vivo": a API só é útil se conseguir falar com o banco.
# Por isso o /health faz um "SELECT 1". Banco fora do ar = 503 (serviço indisponível),
# e o healthcheck do Docker marca a API como "unhealthy".
@app.get("/health", tags=["saúde"])
def health(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "versao": VERSAO, "banco": "ok"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "erro", "versao": VERSAO, "banco": "indisponível"}


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
