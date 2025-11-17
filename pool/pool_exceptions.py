"""Pool-specific exceptions."""
from uuid import UUID


class PoolNotFoundError(Exception):
    """Raised when a pool is not found."""

    def __init__(self, pool_id: UUID):
        self.pool_id = pool_id
        super().__init__(f"Pool {pool_id} not found")


class MemberNotFoundError(Exception):
    """Raised when a pool member is not found."""

    def __init__(self, pool_id: UUID, user_id: UUID):
        self.pool_id = pool_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is not a member of pool {pool_id}")


class MemberAlreadyExistsError(Exception):
    """Raised when attempting to add a member that already exists."""

    def __init__(self, pool_id: UUID, user_id: UUID):
        self.pool_id = pool_id
        self.user_id = user_id
        super().__init__(f"User {user_id} is already a member of pool {pool_id}")
