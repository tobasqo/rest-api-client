from pydantic import BaseModel, HttpUrl, ValidationError

from apix.exceptions import ApixInvalidUrlError


class UrlValidator(BaseModel):
    url: HttpUrl


def parse_url(url: str) -> str:
    try:
        # noinspection PyTypeChecker
        _ = UrlValidator(url=url)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise ApixInvalidUrlError(url) from exc

    return url.rstrip("/")
