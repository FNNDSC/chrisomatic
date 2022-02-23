class BaseClientError(Exception):
    pass


class ResponseError(BaseClientError):
    pass


class BadRequestError(ResponseError):
    pass


class InternalServerError(ResponseError):
    pass


class IncorrectLoginError(BaseClientError):
    pass


class DeserializationError(BaseClientError):
    pass


class EmptySearchError(BaseClientError):
    pass


class PluralResultsError(BaseClientError):
    pass
