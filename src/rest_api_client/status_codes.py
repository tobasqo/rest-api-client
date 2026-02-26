from __future__ import annotations

from httpx._status_codes import codes


class HttpStatusCode:
    def __init__(self, value: int, phrase: str = "") -> None:
        self.value = value
        self.phrase = phrase

    @classmethod
    def from_value(cls, value: int) -> HttpStatusCode:
        phrase = codes.get_reason_phrase(value) or "Unknown error"
        return cls(value, phrase)

    def __str__(self) -> str:
        return f"{self.value} - {self.phrase}"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HttpStatusCode):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other: HttpStatusCode) -> bool:
        return self.value < other.value

    def __le__(self, other: HttpStatusCode) -> bool:
        return self.value <= other.value

    def __gt__(self, other: HttpStatusCode) -> bool:
        return self.value > other.value

    def __ge__(self, other: HttpStatusCode) -> bool:
        return self.value >= other.value

    def __hash__(self) -> int:
        return hash(self.value)
