from database import models  # noqa: F401
from database.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
