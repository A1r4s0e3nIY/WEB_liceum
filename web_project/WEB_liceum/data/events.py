import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Event(SqlAlchemyBase):
    __tablename__ = "events"

    eid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.uid"))
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    year = sqlalchemy.Column(sqlalchemy.Integer)
    month = sqlalchemy.Column(sqlalchemy.Integer)
    day = sqlalchemy.Column(sqlalchemy.Integer)