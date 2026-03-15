from pydantic import BaseModel, HttpUrl, ValidationError

from rest_api_client.exceptions import RestApiInvalidUrlError


class BaseUrl(BaseModel):
    url: HttpUrl


def parse_url(url: str) -> str:
    try:
        # noinspection PyTypeChecker
        _ = BaseUrl(url=url)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise RestApiInvalidUrlError(url) from exc

    if url.endswith("/"):
        return url[:-1]

    return url if not url.endswith("/") else url[:-1]
