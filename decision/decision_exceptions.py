"""Decision-specific exceptions."""
from uuid import UUID


class DecisionNotFoundError(Exception):
    """Raised when a decision is not found."""

    def __init__(self, match_id: UUID, user_id: UUID):
        self.match_id = match_id
        self.user_id = user_id
        super().__init__(f"Decision not found for match {match_id}, user {user_id}")


class UnauthorizedDecisionError(Exception):
    """Raised when a user tries to make a decision they're not authorized for."""

    def __init__(self, user_id: UUID, match_id: UUID):
        self.user_id = user_id
        self.match_id = match_id
        super().__init__(f"User {user_id} is not authorized to decide on match {match_id}")


class MatchNotFoundError(Exception):
    """Raised when referenced match is not found."""

    def __init__(self, match_id: UUID):
        self.match_id = match_id
        super().__init__(f"Match {match_id} not found")
