from typing import Any, Dict


class AuthToken:
    def __init__(self, user: str, signature: str):
        self.user = user
        self.signature = signature

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthToken':
        return cls(
            user=data.get("user", ""),
            signature=data.get("signature", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "signature": self.signature
        }
    