"""Formato dos dados que ENTRAM e SAEM da API (com validação automática).

Se alguém mandar idade = -3 ou nome vazio, o FastAPI recusa sozinho com erro 422,
antes mesmo de chegar no banco.
"""
from pydantic import BaseModel, ConfigDict, Field


class PetBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100, examples=["Rex"])
    especie: str = Field(min_length=1, max_length=50, examples=["Cachorro"])
    raca: str = Field(min_length=1, max_length=100, examples=["Vira-lata"])
    idade: int = Field(ge=0, le=100, examples=[3])  # ge = maior ou igual, le = menor ou igual
    tutor: str = Field(min_length=1, max_length=100, examples=["Ana"])


class PetCreate(PetBase):
    """O que o cliente envia para cadastrar ou editar."""


class PetOut(PetBase):
    """O que a API devolve: os dados + o id."""
    model_config = ConfigDict(from_attributes=True)  # permite converter direto da tabela
    id: int
