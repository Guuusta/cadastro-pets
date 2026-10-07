"""API de Cadastro de Pets: as rotas do CRUD."""
import os
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .logs import configurar_logs, request_id_atual
from .metricas import DURACAO, OPERACOES_PETS, PEDIDOS

VERSAO = "0.5.0"

log = configurar_logs()

# Cria a tabela "pets" se ela ainda não existir
Base.metadata.create_all(bind=engine)

# ROOT_PATH: o "endereço base" quando a API está atrás de um proxy.
# Atrás do Nginx ela mora em /api, então a página /docs precisa saber disso
# para montar os links certos (/api/openapi.json). Sem proxy, fica vazio.
app = FastAPI(title="Cadastro de Pets - API", version=VERSAO, root_path=os.getenv("ROOT_PATH", ""))


@app.middleware("http")
async def registrar_pedido(request: Request, call_next):
    """Registra UMA linha de log por pedido, com o "número de protocolo" (request_id).

    O proxy manda o request_id no cabeçalho X-Request-ID. Assim, a linha do proxy e a
    linha da API do MESMO pedido têm o mesmo número. Sem proxy, a API gera um.
    """
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request_id_atual.set(request_id)                    # todos os logs deste pedido levam o número
    inicio = time.perf_counter()
    resposta = await call_next(request)
    resposta.headers["X-Request-ID"] = request_id      # devolve o número para quem chamou
    duracao = time.perf_counter() - inicio

    # Métricas: usamos o MOLDE da rota (/pets/{pet_id}) e não o caminho real (/pets/7),
    # senão cada pet viraria uma linha nova no Prometheus
    rota = getattr(request.scope.get("route"), "path", "desconhecida")
    if rota not in ("/health", "/metrics"):
        PEDIDOS.labels(request.method, rota, str(resposta.status_code)).inc()
        DURACAO.labels(request.method, rota).observe(duracao)

    # O healthcheck chama /health a cada 10s: não vale a pena sujar o log com isso
    if request.url.path not in ("/health", "/metrics"):
        log.info("pedido atendido", extra={"campos": {
            "metodo": request.method,
            "caminho": request.url.path,
            "status": resposta.status_code,
            "duracao_ms": round(duracao * 1000, 1),
            "ip_cliente": request.headers.get("X-Real-IP", request.client.host if request.client else None),
        }})
    return resposta


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
        log.error("banco indisponível no health check", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "erro", "versao": VERSAO, "banco": "indisponível"}


# ---------- Métricas (lidas pelo Prometheus pela rede interna) ----------
# O proxy BLOQUEIA /api/metrics: de fora ninguém vê; só o Prometheus, por dentro
@app.get("/metrics", include_in_schema=False)
def metricas():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------- C: criar ----------
@app.post("/pets", response_model=schemas.PetOut, status_code=status.HTTP_201_CREATED, tags=["pets"])
def criar_pet(dados: schemas.PetCreate, db: Session = Depends(get_db)):
    pet = models.Pet(**dados.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)          # pega o id que o banco gerou
    OPERACOES_PETS.labels("cadastro").inc()
    log.info("pet cadastrado", extra={"campos": {"pet_id": pet.id, "nome": pet.nome}})
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
    OPERACOES_PETS.labels("atualizacao").inc()
    log.info("pet atualizado", extra={"campos": {"pet_id": pet.id, "nome": pet.nome}})
    return pet


# ---------- D: apagar ----------
@app.delete("/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["pets"])
def apagar_pet(pet_id: int, db: Session = Depends(get_db)):
    pet = buscar_pet(pet_id, db)
    db.delete(pet)
    db.commit()
    OPERACOES_PETS.labels("exclusao").inc()
    log.info("pet excluído", extra={"campos": {"pet_id": pet_id, "nome": pet.nome}})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
