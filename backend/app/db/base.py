from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import ORM models so metadata is complete for Alembic and tests.
from app.auth import models as auth_models  # noqa: E402,F401
from app.profiles import models as profile_models  # noqa: E402,F401
from app.foods import models as food_models  # noqa: E402,F401
