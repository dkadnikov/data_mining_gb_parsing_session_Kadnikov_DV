import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=self.engine)
        self.maker = sessionmaker(bind=self.engine)

    def get_or_create(self, session, model, **kwargs):
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            return instance

    def add_post(self, data):
        session = self.maker()
        post = models.Post(
            **data["post_data"],
            author=self.get_or_create(session, models.Author, **data["author_data"]),
            tags=[self.get_or_create(session, models.Tag, **tag_params) for tag_params in data["tags_data"]],
            comments=[models.Comment(**comment_params) for comment_params in data["comments_data"]]
        )
        for itm in post.tags:
            itm.posts.append(post)
        for itm in post.comments:
            if itm.parent_id:
                itm.parent = session.query(models.Comment).filter_by(id=itm.parent_id).first()

        try:
            session.add(post)
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
        finally:
            session.close()