from django.conf import settings


users_collection=settings.MONGO_DB["users"]
products_collection=settings.MONGO_DB["products"]
carts_collection=settings.MONGO_DB["carts"]