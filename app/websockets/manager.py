from fastapi import WebSocket, WebSocketDisconnect, status
from typing import List, Dict, Any
import logging
import asyncio
import traceback

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)
        logger.info(f"New connection added. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Connection removed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            logger.error(traceback.format_exc())
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return
            
        disconnected_websockets = []
        
        # Create tasks for all connections
        tasks = [self._send_to_connection(connection, message, disconnected_websockets) 
                 for connection in self.active_connections]
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up disconnected websockets after iteration
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
            
    async def _send_to_connection(self, connection: WebSocket, message: Dict[str, Any], 
                                 disconnected_websockets: List[WebSocket]):
        """Helper method to send a message to a single connection."""
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error during broadcast to a connection: {str(e)}")
            logger.error(traceback.format_exc())
            disconnected_websockets.append(connection)

    async def send_to_connections(self, message: Dict[str, Any], connections: List[WebSocket]):
        if not connections:
            logger.debug("No connections to send message to")
            return
            
        disconnected_websockets = []
        
        # Create tasks for all specified connections
        tasks = [self._send_to_connection(connection, message, disconnected_websockets) 
                 for connection in connections]
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up disconnected websockets after iteration
        for websocket in disconnected_websockets:
            self.disconnect(websocket)


manager = ConnectionManager()