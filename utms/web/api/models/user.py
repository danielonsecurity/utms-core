from pydantic import BaseModel
from typing import List

class CurrentUser(BaseModel):
    id: str
    username: str
    roles: List[str] = []

    def is_admin(self, admin_role_name: str) -> bool:
        """Checks if the specified admin role is in the user's list of roles."""
        return admin_role_name in self.roles
