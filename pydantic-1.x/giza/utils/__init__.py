import json
from typing import Any, Dict

from requests import Response

from giza.utils.echo import Echo

# Provided an instance for ease of use
echo = Echo()

REQUEST_ID_HEADER = "x-request-id"


def get_response_info(response: Response | None) -> Dict[str, Any]:
    """
    Utility to retrieve information of the client response.

    Try to get the body, if not just get the text.

    Args:
        response (Response): a response from the API

    Returns:
        dict: information about the returned response
    """
    if response is None:
        return {
            "content": "",
            "detail": "",
            "status_code": 999,
            "request_id": "",
        }
    try:
        request_id = response.headers.get(REQUEST_ID_HEADER, None)
        content = response.json()
        detail = content.get("detail", content.get("message", ""))
    except json.JSONDecodeError:
        content = response.text if len(response.text) < 255 else response.text[:255]
        detail = ""

    return {
        "content": content,
        "detail": detail,
        "status_code": response.status_code,
        "request_id": request_id,
    }
