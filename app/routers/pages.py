from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@router.get("/messages", response_class=HTMLResponse)
async def read_messages(request: Request):
    message_list = [
        {"id": 1, "content": "Hello, this is a test message."},
        {"id": 2, "content": "Another message for testing."},
        {"id": 3, "content": "FastAPI is great for building APIs."},
    ]

    return templates.TemplateResponse("messages.html", {"request": request, "messages": message_list, "page_title": "Messages"})

@router.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", 
        {
            "request": request, 
            "page_title": "Real-time Chat"
        }
    )