"""خطاهای سفارشی پروژه."""


class LMSError(Exception):
    """خطای پایه LMS Assistant."""
    pass


class AuthenticationError(LMSError):
    """خطای احراز هویت."""
    pass


class ConnectionError(LMSError):
    """خطای اتصال به LMS."""
    pass


class ParseError(LMSError):
    """خطای Parse کردن HTML."""
    pass


class StorageError(LMSError):
    """خطای دیتابیس."""
    pass