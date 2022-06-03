from django.db import models

# Create your models here.
from django.http import HttpResponse

from AppBase.model import AppBaseModel


class Product(AppBaseModel):
    key = models.CharField(max_length=8)
    name = models.CharField(max_length=100, null=True)
    price = models.IntegerField(default=0)
    description = models.CharField(max_length=75, null=True)
    available = models.BooleanField(default=True,)

    def api(self):
        return {
            "key": self.key,
            "name": self.name,
            "price": self.description,
            "available": self.available
        }

    def save(self, *args, **kwargs):
        if not self.pk:
            self.key = Product.genfixedkey(8, field='key')
        super(Product, self).save(*args, **kwargs)
