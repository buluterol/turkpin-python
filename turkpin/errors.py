class TurkpinError(Exception):
    """API error code other than "000", or an HTTP / XML failure (code is then empty)."""

    def __init__(self, message: str, code: str = ""):
        super().__init__(message)
        self.code = code
