from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table, DateTime

from .mixins import UrlMixin


Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(Base, UrlMixin):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(250), nullable=False, unique=False)
    img_url = Column(String, unique=False, nullable=True)
    date_published = Column(DateTime, unique=False, nullable=True)
    author_id = Column(Integer, ForeignKey("author.id"), nullable=True)
    author = relationship("Author", backref="posts")
    tags = relationship("Tag", secondary=tag_post)


class Author(Base, UrlMixin):
    __tablename__ = "author"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)


class Tag(Base, UrlMixin):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    posts = relationship(Post, secondary=tag_post)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(Text, nullable=False, unique=False)
    created_at = Column(DateTime, unique=False, nullable=True)
    author_of_comment = Column(String(150), nullable=False)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    post = relationship(Post, backref="comments")
    parent = relationship("Comment", uselist=False, post_update=True)