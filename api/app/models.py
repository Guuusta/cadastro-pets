"""Tabela do banco de dados: como um pet é GUARDADO."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Pet(Base):
    __tablename__ = "pets"                                      # nome da tabela no banco

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # número único, gerado pelo banco
    nome: Mapped[str] = mapped_column(String(100))
    especie: Mapped[str] = mapped_column(String(50))            # cachorro, gato...
    raca: Mapped[str] = mapped_column(String(100))
    idade: Mapped[int] = mapped_column(Integer)                 # em anos
    tutor: Mapped[str] = mapped_column(String(100))             # nome do dono
