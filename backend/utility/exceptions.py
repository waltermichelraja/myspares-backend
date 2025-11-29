from functools import wraps
from pymongo.errors import PyMongoError
from rest_framework.response import Response
from rest_framework import status


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PyMongoError as e:
            return Response({"error": "database error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": "internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper