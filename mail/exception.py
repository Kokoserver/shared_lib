from jinja2 import TemplateNotFound


class InvalidCredentialError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidEmailContentError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EmailTemplateNotFoundError(TemplateNotFound):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class TemplateFolderNotFoundError(NotADirectoryError):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class EmailSendingError(NotADirectoryError):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
