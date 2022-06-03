from django.urls import path
from Platform.api import*


urlpatterns = [
    path("add_product", add_product),
    path("edit_product", edit_product),
    path("delete_product", delete_product),
    path("make_not_available_product", make_not_available_product),
   ]
