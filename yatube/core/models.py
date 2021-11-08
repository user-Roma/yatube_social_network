from django.db import models
from django.db.models.fields import DateTimeField


class CreatedModel(models.Model):
    """Abctract model - adds date/time created"""
    created = DateTimeField(
        'time happened',
        auto_now_add=True,
    )

    class Meta:
        abstract = True
