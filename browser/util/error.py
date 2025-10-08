from typing import Any


class BusinessError(Exception):

    def __init__(self, message: str, code: str = None, details: Any = None):
        self.message = message
        self.code = code
        self.details = details

    def __str__(self):
        if self.code:
            return f"{self.code}: {self.message or 'None'}"

        return self.message or "None"

    def __repr__(self):
        return f"BusinessError({self.message!r}, {self.code!r}, {self.details!r})"


class InternalError(Exception):
    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"InternalError({self.message!r}, {self.details!r})"
