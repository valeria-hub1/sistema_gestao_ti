from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Text,
    Numeric,
    ForeignKey
)

from sqlalchemy.orm import relationship

from models.conexao import Base


class Suporte(Base):
    __tablename__ = "suportes"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_equipamento = Column(
        Integer,
        ForeignKey("equipamentos.id"),
        nullable=False
    )

    data_suporte = Column(
        Date,
        nullable=False
    )

    tipo_suporte = Column(
        String(100),
        nullable=False
    )

    descricao = Column(
        Text,
        nullable=False
    )

    responsavel = Column(
        String(200),
        nullable=False
    )

    custo = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    equipamento = relationship(
        "Equipamento",
        backref="suportes"
    )
