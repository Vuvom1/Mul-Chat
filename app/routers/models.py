from pydantic import BaseModel

class MsgPayload(BaseModel):
    msg_id: int
    msg_name: str

class MessageResponse(BaseModel):
    message: MsgPayload

class MessagesListResponse(BaseModel):
    messages: dict[int, MsgPayload]

class SendMessageRequest(BaseModel):
    user_id: int
    group_id: int
    message: str

class JoinGroupRequest(BaseModel):
    user_id: int
    group_id: int = None
    group_name: str = None

class CreateGroupRequest(BaseModel):
    group_name: str
    description: str = None

class ClientInfo(BaseModel):
    client_id: str
    username: str
    joined_groups: list[str]

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
