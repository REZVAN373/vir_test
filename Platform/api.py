import json

from django.views.decorators.csrf import csrf_exempt

from AppBase.response import rest
from Platform.models import Product

TOKEN = "lrideksjuwednjke"


@rest
@csrf_exempt
def add_product(request):
    try:
        d = json.loads(request.body.decode('utf-8'))
        name = d['name']
        price = int(d['price'])
        descriptions = d['descriptions'] if "descriptions" in d.keys() else ""
        token = d['token']

        validate = 3 < len(name) < 30 and len(descriptions) < 75
        if not validate:
            raise Exception

    except:
        return 400

    if token != TOKEN:
        return 401

    try:
        p = Product(name=name, price=price, description=descriptions)
        p.save()
        return 200
    except:
        return 502


@rest
@csrf_exempt
def edit_product(request):
    try:
        d = json.loads(request.body.decode('utf-8'))
        id = d['id']
        name = d['name']
        price = int(d['price'])
        description = d['description'] if 'description' in d.keys() else ''
        token = d['token']

        validate = 3 < len(name) < 30 and len(description) < 75
        if not validate:
            raise Exception
    except:
        return 400

    if token != TOKEN:
        return 401

    try:
        product = Product.objects.get(id=id)
        product.name = name
        product.price = price
        product.description = description
        product.save()
        return 200
    except:
        return 502


@rest
@csrf_exempt
def delete_product(request):
    try:
        d = json.loads(request.body.decode('utf-8'))
        id = int(d['id'])
        token = d['token']

        if not id:
            raise Exception

    except:
        return 400

    if token != TOKEN:
        return 401

    try:
        product = Product.objects.get(id=id)
        product.delete()
    except:
        return 501


@rest
@csrf_exempt
def make_not_available_product(request):
    try:
        d = json.loads(request.body.decode('utf-8'))
        id = int(d['id'])
        token = d['token']

        if not id:
            raise Exception

    except:
        return 400

    if token != TOKEN:
        return 401

    try:
        product = Product.objects.get(id=id)
        product.available = False
        product.save()
    except:
        return 501
