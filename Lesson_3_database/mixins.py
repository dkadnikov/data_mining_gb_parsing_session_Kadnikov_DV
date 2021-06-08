from sqlalchemy import Column, Integer, String


class IdMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


class UrlMixin:
    url = Column(String, unique=True, nullable=False)