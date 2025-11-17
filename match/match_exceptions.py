"""Match-specific exceptions."""
from uuid import UUID


class MatchNotFoundError(Exception):
    """Raised when a match is not found."""

    def __init__(self, match_id: UUID):
        self.match_id = match_id
        super().__init__(f"Match {match_id} not found")


class InvalidMatchError(Exception):
    """Raised when match creation or update is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class DuplicateMatchError(Exception):
    """Raised when attempting to create a duplicate match."""

    def __init__(self, pool_id: UUID, user1_id: UUID, user2_id: UUID):
        self.pool_id = pool_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        super().__init__(
            f"Match already exists between {user1_id} and {user2_id} in pool {pool_id}"
        )


class UserNotInPoolError(Exception):
    """Raised when a user is not a member of the specified pool."""

    def __init__(self, user_id: UUID, pool_id: UUID):
        self.user_id = user_id
        self.pool_id = pool_id
        super().__init__(f"User {user_id} is not a member of pool {pool_id}")
