# FastAPI SSR Project

This project is a FastAPI application that implements server-side rendering (SSR) using Jinja2 templates. It serves dynamic content by rendering HTML pages on the server before sending them to the client.

## Project Structure

```
fastapi-ssr-project
├── app
│   ├── main.py               # Entry point of the FastAPI application
│   ├── models.py             # Data models used in the application
│   ├── templates             # HTML templates for rendering
│   │   ├── base.html         # Base HTML template
│   │   ├── index.html        # Home page template
│   │   ├── about.html        # About page template
│   │   └── messages.html     # Messages page template
│   ├── static                # Static files (CSS, JS)
│   │   ├── css
│   │   │   └── style.css     # CSS styles for the application
│   │   └── js
│   │       └── main.js       # JavaScript code for client-side interactions
│   └── routers               # Route definitions
│       └── pages.py          # Routes for rendering templates
├── tests                     # Test files
│   └── test_main.py          # Tests for the application
├── .env                      # Environment variables
├── .gitignore                # Files to ignore in version control
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fastapi-ssr-project
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:8000`.

## Usage

- The home page is accessible at `/`.
- The about page can be found at `/about`.
- Messages can be accessed at `/messages`.

## Testing

To run the tests, use the following command:

```bash
pytest tests/test_main.py
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.