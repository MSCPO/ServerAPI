from tortoise import fields
from tortoise.models import Model

from app.db import add_model

add_model(__name__)


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    hashed_password = fields.CharField(max_length=128)

    class Meta:
        table = "users"
