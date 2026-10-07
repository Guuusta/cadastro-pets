"""Testes automáticos da API. Rodam no CI (fase 8) a cada push.

Usam um banco SQLite temporário, então não precisam de Postgres para rodar.
"""
import os
import tempfile

# Banco de teste: um arquivo temporário (configurado ANTES de importar a app)
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/teste.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

cliente = TestClient(app)
REX = {"nome": "Rex", "especie": "Cachorro", "raca": "Vira-lata", "idade": 3, "tutor": "Ana"}


def test_health():
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_crud_completo():
    # Create
    r = cliente.post("/pets", json=REX)
    assert r.status_code == 201
    pet_id = r.json()["id"]

    # Read
    assert cliente.get(f"/pets/{pet_id}").json()["nome"] == "Rex"
    assert any(p["id"] == pet_id for p in cliente.get("/pets").json())

    # Update
    r = cliente.put(f"/pets/{pet_id}", json={**REX, "idade": 4})
    assert r.status_code == 200
    assert r.json()["idade"] == 4

    # Delete
    assert cliente.delete(f"/pets/{pet_id}").status_code == 204
    assert cliente.get(f"/pets/{pet_id}").status_code == 404


def test_validacao_idade_negativa():
    r = cliente.post("/pets", json={**REX, "idade": -1})
    assert r.status_code == 422


def test_pet_inexistente():
    assert cliente.get("/pets/99999").status_code == 404
