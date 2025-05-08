from fastapi.responses import JSONResponse
from fastapi import status


def json_response(data=None, message="", code=0, http_status=status.HTTP_200_OK):
    """
    Standard JSON response format.
    :param data: Response data payload
    :param message: Message string
    :param code: Application-specific code, 0 means success
    :param http_status: HTTP status code
    """
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": message,
            "data": data,
        },
    )


def error_response(message, code=1, http_status=status.HTTP_400_BAD_REQUEST):
    """
    Standard error response.
    """
    return json_response(data=None, message=message, code=code, http_status=http_status)


def not_found_response(message="Not Found", code=404):
    return error_response(message=message, code=code, http_status=status.HTTP_404_NOT_FOUND)


def validation_error_response(message="Validation Error", code=422):
    return error_response(message=message, code=code, http_status=status.HTTP_422_UNPROCESSABLE_ENTITY)
