class DomainError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserAlreadyExists(DomainError):
    def __init__(self) -> None:
        super().__init__("Email or username already registered.")


class InvalidCredentials(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid login or password.")


class UserInactive(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid login or password.")


class InvalidToken(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid or expired refresh token.")


class UserNotFound(DomainError):
    def __init__(self) -> None:
        super().__init__("User not found.")


class LastAdminProtected(DomainError):
    def __init__(self) -> None:
        super().__init__("The last active admin cannot be removed or demoted.")


class CannotDeleteSelf(DomainError):
    def __init__(self) -> None:
        super().__init__("You cannot delete your own account.")


class WeakPassword(DomainError):
    pass


class InvalidUsername(DomainError):
    pass


class InvalidEmail(DomainError):
    pass


class CurrentPasswordIncorrect(DomainError):
    def __init__(self) -> None:
        super().__init__("Current password is incorrect.")


class NoChangesProvided(DomainError):
    def __init__(self) -> None:
        super().__init__("Provide a role or active status to update.")
