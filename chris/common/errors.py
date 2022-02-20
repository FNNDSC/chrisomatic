class BaseClientError(Exception):
    pass


class BadRequestError(BaseClientError):
    pass


class IncorrectLoginError(BaseClientError):
    pass


class DeserializationError(BaseClientError):
    pass


class EmptySearchError(BaseClientError):
    pass


class PluralResultsError(BaseClientError):
    pass
