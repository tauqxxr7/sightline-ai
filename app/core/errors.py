"""Safe, actionable errors that can cross the local API boundary."""


class SightLineError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code = code
        self.status = status
