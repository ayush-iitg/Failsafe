# Makes 'models' a Python package
# Import all models here so Alembic can discover them for migrations
from app.models.db_models import User, Student, Prediction, Intervention
