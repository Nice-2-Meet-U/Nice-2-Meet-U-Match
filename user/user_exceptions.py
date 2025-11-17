"""User-specific exceptions."""
from uuid import UUID


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class UserNotInPoolError(Exception):
    """Raised when a user is not in any pool."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id
        super().__init__(f"User {user_id} is not a member of any pool")
