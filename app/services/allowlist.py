
class ContactAllowlist:
    def __init__(self, allowed_contacts: set[str]) -> None:
        self._allowed_contacts = allowed_contacts

    def is_allowed(self, contact_id: str) -> bool:
        if not self._allowed_contacts:
            return False
        return contact_id in self._allowed_contacts
