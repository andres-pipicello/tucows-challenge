from sqlalchemy import ForeignKey, DECIMAL, create_engine
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase, Mapped, mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Graph(Base):
    __tablename__ = 'graphs'

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class Node(Base):
    __tablename__ = 'nodes'

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_id: Mapped[str] = mapped_column(ForeignKey('graphs.id'))
    name: Mapped[str]


class Edge(Base):
    __tablename__ = 'edges'

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_id: Mapped[str] = mapped_column(ForeignKey('graphs.id'))
    from_node_id: Mapped[str] = mapped_column(ForeignKey('nodes.id'), index=True)
    to_node_id: Mapped[str] = mapped_column(ForeignKey('nodes.id'), index=True)
    cost: Mapped[float] = mapped_column(DECIMAL)


def local_postgres_engine():
    return create_engine("postgresql+psycopg2://user:password@localhost:5432/tucows", echo=True)
