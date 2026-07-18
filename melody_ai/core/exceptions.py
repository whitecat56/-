class MelodyError(Exception):
    pass


class NotFoundError(MelodyError):
    pass


class PermissionDeniedError(MelodyError):
    pass


class ProviderUnavailableError(MelodyError):
    pass


class ValidationError(MelodyError):
    pass
