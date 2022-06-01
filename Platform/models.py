from django.db import models

# Create your models here.
from AppBase.model import AppBaseModel


class Product(AppBaseModel):
    key = models.CharField(max_length=8)
    name = models.CharField(max_length=100, null=True)
    price = models.IntegerField(default=0)
    description = models.CharField(max_length=75, null=True)
