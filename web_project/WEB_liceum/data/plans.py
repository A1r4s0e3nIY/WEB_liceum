import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Plan(SqlAlchemyBase):
    __tablename__ = "plans"

    pid = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.uid"))
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
