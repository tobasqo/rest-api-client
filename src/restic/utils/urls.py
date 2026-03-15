from pydantic import BaseModel, HttpUrl, ValidationError

from restic.exceptions import ResticInvalidUrlError


class UrlValidator(BaseModel):
    url: HttpUrl


def parse_url(url: str) -> str:
    try:
        # noinspection PyTypeChecker
        _ = UrlValidator(url=url)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise ResticInvalidUrlError(url) from exc

    return url.rstrip("/")
