from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        errors = response.data

        first_error = None
        for field, messages in errors.items():
            if isinstance(messages, list) and messages:
                first_error = f"{field}: {messages[0]}" if field != "non_field_errors" else messages[0]
                break
            elif isinstance(messages, str):
                first_error = messages
                break

        if first_error:
            response.data = {"error": str(first_error)}

    return response