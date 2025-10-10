import logging
from django.conf import settings


users_collection=settings.MONGO_DB["users"]
users_collection.create_index("phone_number", unique=True)

blacklisted_tokens_collection=settings.MONGO_DB["blacklisted_tokens"]

temporary_users_collection=settings.MONGO_DB["temporary_users"]

logger=logging.getLogger("authentication_events")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch=logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)