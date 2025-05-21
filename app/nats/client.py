import nats 
import asyncio
import json
import uuid
import os
from dotenv import load_dotenv
from nats.aio.client import Client
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

class ChatClient:
    def __init__(self, server_url=None, username=None):
        self.server_url = server_url or os.getenv("NATS_SERVER_URL", "nats://0.0.0.0:4222")
        self.username = username or os.getenv("DEFAULT_USERNAME") or f"user_{uuid.uuid4().hex[:8]}"
        self.client_id = str(uuid.uuid4())
        self.nc = Client()
        self.chat_channel = os.getenv("CHAT_CHANNEL", "chat.general")
        self.private_channel = f"chat.private.{self.client_id}"

        self.subcriptions: Dict[str, Any] = {}
        self.joined_groups: Dict[str, Any] = {}

        self.channel_handlers: Dict[str, Any] = {}
        
    async def connect(self):
        await self.nc.connect(self.server_url)
        print(f"Connected to NATS server as {self.username}")
        
        # Subscribe to private messages
        await self.nc.subscribe(self.private_channel, cb=self.private_message_handler)
        
        # Announce join
        join_msg = {
            "type": "join",
            "sender": self.username,
            "sender_id": self.client_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.nc.publish(self.chat_channel, json.dumps(join_msg).encode())

    async def subcribe_to_channel(self, channel: str, message_handler=None):
        if channel in self.subcriptions:
            print(f"Already subscribed to {channel}")
            return
        
        subcription = await self.nc.subscribe(channel, cb=message_handler)
        self.subcriptions[channel] = subcription

        print(f"Subscribed to {channel}")
        return subcription
    
    async def unsubcribe_from_channel(self, channel: str):
        if channel not in self.subcriptions:
            print(f"Not subscribed to {channel}")
            return
        
        await self.subcriptions[channel].unsubscribe()
        
        del self.subcriptions[channel]
        if channel in self.channel_handlers[channel]:
            del self.channel_handlers[channel]
    
    async def join_group(self, group_name: str):
        if not group_name.startswith("chat."):
            group_channel = f"chat.{group_name}"
        else:
            group_channel = group_name

        if group_channel in self.joined_groups:
            print(f"Already joined group {group_name}")
            return
        
        await self.subcribe_to_channel(group_channel)

        self.joined_groups[group_channel] = group_name

        join_msg = {
            "type": "join",
            "sender": self.username,
            "sender_id": self.client_id,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.nc.publish(group_channel, json.dumps(join_msg).encode())
    
    async def message_handler(self, msg):
        data = json.loads(msg.data.decode())
        if data.get("sender_id") != self.client_id:
            if data.get("type") == "join":
                print(f">> {data['sender']} has joined the chat")
            elif data.get("type") == "leave":
                print(f">> {data['sender']} has left the chat")
            else:
                print(f"{data['sender']}: {data['message']}")
    
    async def private_message_handler(self, msg):
        data = json.loads(msg.data.decode())
        print(f"[PRIVATE] {data['sender']}: {data['message']}")

    async def send_group_message(self, group_name, message):
        if not group_name.startswith("chat."):
            group_channel = f"chat.{group_name}"
        else:
            group_channel = group_name

        if group_channel not in self.joined_groups:
            print(f"Not joined to group {group_name}")
            return
        
        msg_data = {
            "type": "message",
            "sender": self.username,
            "sender_id": self.client_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.nc.publish(group_channel, json.dumps(msg_data).encode())
    
    async def send_message(self, message):
        msg_data = {
            "type": "message",
            "sender": self.username,
            "sender_id": self.client_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.nc.publish(self.chat_channel, json.dumps(msg_data).encode())
    
    async def send_private_message(self, recipient_id, message):
        msg_data = {
            "type": "private",
            "sender": self.username,
            "sender_id": self.client_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.nc.publish(f"chat.private.{recipient_id}", json.dumps(msg_data).encode())

    
    
    async def disconnect(self):
        leave_msg = {
            "type": "leave",
            "sender": self.username,
            "sender_id": self.client_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.nc.publish(self.chat_channel, json.dumps(leave_msg).encode())
        await self.nc.drain()