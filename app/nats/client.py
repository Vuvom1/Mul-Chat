import nats 
import asyncio
import json
import uuid
import os
from dotenv import load_dotenv
from nats.aio.client import Client
from typing import Dict, Any
from app.shared.auth_token import AuthToken

# Load environment variables from .env file
load_dotenv()

class ChatClient:
    def __init__(self, server_url=None, username=None, auth_token=None, client_id=None):
        self.server_url = server_url or os.getenv("NATS_SERVER_URL", "nats://0.0.0.0:4222")
        self.username = username or os.getenv("DEFAULT_USERNAME") or f"user_{uuid.uuid4().hex[:8]}"
        self.client_id = client_id or str(uuid.uuid4())
        self.auth_token = auth_token
        self.nc = Client()
        self.chat_channel = os.getenv("CHAT_CHANNEL", "chat.general")
        self.private_channel = f"chat.private.{self.client_id}"

        self.subscriptions: Dict[str, Any] = {}
        self.joined_groups: Dict[str, Any] = {}

        self.channel_handlers: Dict[str, Any] = {}
        
    async def connect(self):
        """
        Connect to NATS server with authentication
        """
        # Prepare connection options with authentication
        connect_opts = {
            "servers": [self.server_url],
            "reconnect_time_wait": 0.5,
            "max_reconnect_attempts": 10,
            "ping_interval": 20,
            "verbose": True,
        }
        
        # Add authentication if available
        if self.auth_token:
            # Convert auth token to string for NATS connection
            auth_token_str = json.dumps(self.auth_token.to_dict())
            
            # Add authentication to connect options
            connect_opts["user"] = self.username
            connect_opts["auth_token"] = auth_token_str
            connect_opts["client_id"] = self.client_id
            connect_opts["user_agent"] = "ChatClient/1.0"
        
        # Connect to NATS server
        await self.nc.connect(**connect_opts)
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

    async def subscribe_to_channel(self, channel: str, message_handler=None):
        """
        Subscribe to a NATS channel
        """
        if channel in self.subscriptions:
            print(f"Already subscribed to {channel}")
            return
        
        subscription = await self.nc.subscribe(channel, cb=message_handler or self.message_handler)
        self.subscriptions[channel] = subscription

        print(f"Subscribed to {channel}")
        return subscription
    
    async def unsubscribe_from_channel(self, channel: str):
        """
        Unsubscribe from a NATS channel
        """
        if channel not in self.subscriptions:
            print(f"Not subscribed to {channel}")
            return
        
        await self.subscriptions[channel].unsubscribe()
        
        del self.subscriptions[channel]
        if channel in self.channel_handlers:
            del self.channel_handlers[channel]
    
    async def join_group(self, group_name: str):
        """
        Join a chat group
        """
        if not group_name.startswith("chat."):
            group_channel = f"chat.{group_name}"
        else:
            group_channel = group_name

        if group_channel in self.joined_groups:
            print(f"Already joined group {group_name}")
            return
        
        await self.subscribe_to_channel(group_channel)

        self.joined_groups[group_channel] = group_name

        join_msg = {
            "type": "join",
            "sender": self.username,
            "sender_id": self.client_id,
            "timestamp": asyncio.get_event_loop().time()
        }

        await self.nc.publish(group_channel, json.dumps(join_msg).encode())
    
    async def leave_group(self, group_name: str):
        """
        Leave a chat group
        """
        if not group_name.startswith("chat."):
            group_channel = f"chat.{group_name}"
        else:
            group_channel = group_name
            
        if group_channel not in self.joined_groups:
            print(f"Not a member of group {group_name}")
            return
            
        leave_msg = {
            "type": "leave",
            "sender": self.username,
            "sender_id": self.client_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.nc.publish(group_channel, json.dumps(leave_msg).encode())
        await self.unsubscribe_from_channel(group_channel)
        
        del self.joined_groups[group_channel]
    
    async def send_message(self, group_name: str, message: str):
        """
        Send a message to a group
        """
        if not group_name.startswith("chat."):
            group_channel = f"chat.{group_name}"
        else:
            group_channel = group_name
            
        if group_channel not in self.joined_groups and group_channel != self.chat_channel:
            print(f"Not a member of group {group_name}. Join the group first.")
            return False
            
        message_data = {
            "type": "message",
            "sender": self.username,
            "sender_id": self.client_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.nc.publish(group_channel, json.dumps(message_data).encode())
        return True
    
    async def send_private_message(self, recipient_id: str, message: str):
        """
        Send a private message to another user
        """
        message_data = {
            "type": "private",
            "sender": self.username,
            "sender_id": self.client_id,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.nc.publish(f"chat.private.{recipient_id}", json.dumps(message_data).encode())
        return True
    
    async def message_handler(self, msg):
        """
        Default message handler for group messages
        """
        data = json.loads(msg.data.decode())
        if data.get("sender_id") != self.client_id:
            if data.get("type") == "join":
                print(f">> {data['sender']} has joined the chat")
            elif data.get("type") == "leave":
                print(f">> {data['sender']} has left the chat")
            else:
                print(f"{data['sender']}: {data['message']}")
    
    async def private_message_handler(self, msg):
        """
        Default message handler for private messages
        """
        data = json.loads(msg.data.decode())
        print(f"[PRIVATE] {data['sender']}: {data['message']}")
        
    async def close(self):
        """
        Close the NATS connection
        """
        # Send leave message to all joined groups
        for group_channel in list(self.joined_groups.keys()):
            leave_msg = {
                "type": "leave",
                "sender": self.username,
                "sender_id": self.client_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.nc.publish(group_channel, json.dumps(leave_msg).encode())
            
        # Close NATS connection
        await self.nc.close()
        print(f"Disconnected from NATS server")