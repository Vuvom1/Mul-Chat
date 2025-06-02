# Mul-Chat: Real-time Chat Platform with NATS

Mul-Chat is a modern real-time chat application built with FastAPI and NATS messaging system. It features user authentication, real-time messaging, chat rooms, and websocket integration for seamless communication.

## Project Overview

This project implements a full-featured chat platform with:
- JWT-based authentication
- Real-time messaging using NATS
- PostgreSQL database for persistence
- Room-based chat organization
- WebSocket support for real-time updates

## Project Structure

```
Mul-Chat
├── app                       # Main application package
│   ├── main.py               # Entry point of the FastAPI application
│   ├── auth                  # Authentication components
│   │   └── dependencies.py   # Auth dependencies and JWT verification
│   ├── database              # Database models and connection
│   │   ├── db.py             # Database connection setup
│   │   └── models.py         # SQLAlchemy ORM models
│   ├── nats                  # NATS messaging integration
│   │   ├── client.py         # NATS client implementation
│   │   └── ncs.py            # NATS Connection Services
│   ├── querries              # Database query functions
│   │   ├── user_querries.py  # User-related database operations
│   │   ├── nats_room_querries.py # Room-related operations
│   │   └── ...               # Other query modules
│   ├── routers               # API routes
│   │   ├── user_router.py    # User authentication routes
│   │   ├── room_router.py    # Chat room management routes
│   │   ├── chat_router.py    # Chat message routes
│   │   └── ...               # Other route modules
│   ├── services              # Business logic
│   │   ├── user_service.py   # User-related logic
│   │   ├── room_service.py   # Room management logic
│   │   ├── chat_service.py   # Chat functionality
│   │   └── ...               # Other service modules
│   ├── templates             # HTML templates for rendering
│   │   ├── base.html         # Base HTML template
│   │   ├── chat.html         # Chat interface
│   │   └── ...               # Other templates
│   ├── static                # Static files (CSS, JS)
│   └── utils                 # Utility functions
│       ├── auth_helpers.py   # Auth-related helpers
│       └── nats_helpers.py   # NATS-related utilities
├── migrations                # Alembic database migrations
├── scripts                   # Utility scripts
│   └── reset_database.py     # Database reset script
├── tests                     # Test files
├── .env                      # Environment variables
├── requirements.txt          # Project dependencies
├── alembic.ini               # Alembic configuration
└── README.md                 # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Mul-Chat.git
   cd Mul-Chat
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory with the following variables:
   ```
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password123
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   
   # NATS
   NATS_URL=nats://localhost:4222
   NATS_USER=default_user
   NATS_PASSWORD=default_password
   
   # JWT Authentication
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Initialize the database:**
   ```bash
   # Reset the database (if needed)
   python scripts/reset_database.py
   
   # Apply migrations
   alembic upgrade head
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:8000`.

## API Endpoints

### Authentication
- **POST /users/create_user** - Register a new user
- **POST /users/login** - Authenticate and get JWT token
- **GET /users/me** - Get current user info (requires authentication)

### Rooms
- **POST /rooms/create_room** - Create a new chat room (requires authentication)
- **POST /rooms/join_room** - Join an existing room (requires authentication)
- **GET /rooms/get_users_in_room/{room_id}** - Get users in a room (requires authentication)
- **DELETE /rooms/leave_room/{room_id}** - Leave a room (requires authentication)

### WebSocket
- **WebSocket /ws/rooms** - Real-time chat connection (requires authentication via token parameter)

## Authentication

The application uses JWT for authentication. To access protected endpoints:

1. First obtain a token by logging in through the `/users/login` endpoint
2. Include the token in the `Authorization` header with the format: `Bearer <your_token>`

Example:
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

For WebSocket connections, include the token as a query parameter:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/rooms?token=${yourToken}`);
```

## NATS Integration

Mul-Chat leverages NATS (Neural Autonomic Transport System) for high-performance messaging:

- **Message Routing**: Messages are routed through NATS subjects based on room names
- **Authentication**: Users are authenticated in NATS using JWT tokens
- **Room Management**: Each chat room has its own NATS subject for isolated messaging
- **Real-time Updates**: Messages are published to NATS and delivered to subscribed clients

## Database Schema

The application uses a PostgreSQL database with the following main tables:

- **users**: User accounts and authentication information
- **nats_accounts**: NATS account information
- **nats_rooms**: Chat room configurations
- **nats_user_rooms**: Many-to-many relationship between users and rooms
- **messages**: Stored chat messages
- **groups**: User groups for organization
- **user_groups**: Many-to-many relationship between users and groups

## Testing

To run the tests, use the following command:

```bash
pytest tests/
```

## Development

### Adding Database Migrations

When making changes to the database models:

```bash
# Create a new migration
alembic revision --autogenerate -m "description_of_changes"

# Apply the migration
alembic upgrade head
```

### Resetting the Database

To reset the database to a clean state:

```bash
python scripts/reset_database.py
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.