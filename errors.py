class HTTPRequestError(Exception):
    """Ошибка статуса запроса."""

    def __init__(self, message,
                 request_url=None,
                 response_code=None,
                 response_body=None):
        """Атрибуты запроса и ответа."""
        self.request_url = request_url
        self.response_code = response_code
        self.response_body = response_body
        super().__init__(message)

    def __str__(self):
        """Выводим сообщение об ошибке и дополнительную информацию."""
        return (f'{super().__str__()}\n',
                f'Request URL: {self.request_url}\n',
                f'Response Code: {self.response_code}\n',
                f'Response Body: {self.response_body}')


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass


class RequestException(Exception):
    """Ошибка при выполнении запроса к API."""

    pass

