from django.conf import settings


users_collection=settings.MONGO_DB["users"]
users_collection.create_index("phone_number", unique=True)

blacklisted_tokens_collection=settings.MONGO_DB["blacklisted_tokens"]