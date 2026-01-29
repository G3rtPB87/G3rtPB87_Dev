# SmargeAI

An intelligent AI agent platform with conversational interface, powered by Google Gemini and built with FastAPI and React.

![SmargeAI](https://img.shields.io/badge/AI-Gemini-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)
![React](https://img.shields.io/badge/React-18.3.1-blue)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4.0-38bdf8)

## Features

- 🤖 **AI-Powered Chat**: Conversational AI using Google Gemini via LangChain
- 🔐 **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- 💬 **Conversation Management**: Create, view, and manage multiple conversation threads
- 📝 **Markdown Support**: Rich text formatting with syntax highlighting for code
- 🌊 **Streaming Responses**: Real-time AI response streaming for better UX
- 🎨 **Premium UI**: Modern dark mode interface with glassmorphism effects
- 📚 **API Documentation**: Auto-generated OpenAPI (Swagger) documentation
- 💾 **Persistent Storage**: SQLite database for users, conversations, and messages

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **LangChain** - AI orchestration framework
- **Google Gemini** - Large Language Model
- **SQLAlchemy** - Async ORM for database operations
- **SQLite** - Lightweight database (easily upgradable to PostgreSQL)
- **JWT** - Secure token-based authentication
- **bcrypt** - Password hashing

### Frontend
- **React 18** - UI library
- **Vite** - Fast build tool and dev server
- **TailwindCSS v4** - Utility-first CSS framework
- **Axios** - HTTP client
- **react-markdown** - Markdown rendering
- **react-syntax-highlighter** - Code syntax highlighting
- **Lucide React** - Icon library

## Prerequisites

- **Python 3.12+** (tested with Python 3.13)
- **Node.js 18+** and npm
- **Google API Key** for Gemini (free tier available)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/G3rtPB87/G3rtPB87_Dev.git
cd G3rtPB87_Dev/smarge_ai
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
# Google Gemini API Key (REQUIRED)
# Get your free API key at: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# JWT Secret Key (REQUIRED for production)
# Generate a secure random string (e.g., using: openssl rand -hex 32)
SECRET_KEY=your_secret_key_change_this_in_production

# Database URL (Optional - defaults to SQLite)
# For SQLite (default): sqlite+aiosqlite:///./smarge_ai.db
# For PostgreSQL: postgresql+asyncpg://user:password@localhost/dbname
DATABASE_URL=sqlite+aiosqlite:///./smarge_ai.db
```

#### Run the Backend Server

```bash
python main.py
```

The backend will start on `http://0.0.0.0:8002`

- **API Documentation**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

### 3. Frontend Setup

Open a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`

### 4. Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8002/docs

## Environment Variables

### Backend (.env)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | ✅ Yes | Google Gemini API key | None |
| `SECRET_KEY` | ⚠️ Production | JWT signing secret (use random string in production) | `your-secret-key-change-this-in-production` |
| `DATABASE_URL` | ❌ No | Database connection string | `sqlite+aiosqlite:///./smarge_ai.db` |

### How to Get Your Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Paste it into your `.env` file as `GOOGLE_API_KEY=your_key_here`

**Note**: The free tier includes generous limits suitable for development and testing.

## Project Structure

```
smarge_ai/
├── backend/
│   ├── venv/                    # Python virtual environment
│   ├── main.py                  # FastAPI application entry point
│   ├── agent.py                 # SmargeAgent with LangChain/Gemini
│   ├── auth.py                  # JWT and password hashing
│   ├── database.py              # SQLAlchemy async engine
│   ├── db_models.py             # User, Conversation, Message models
│   ├── crud.py                  # Database operations
│   ├── models.py                # Pydantic request/response models
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variables template
│   └── smarge_ai.db            # SQLite database (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthPage.jsx     # Login/Register UI
│   │   │   └── ChatInterface.jsx # Main chat interface
│   │   ├── App.jsx              # React router and main app
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # TailwindCSS + custom styles
│   ├── public/
│   ├── package.json             # Node dependencies
│   ├── vite.config.js           # Vite configuration
│   ├── tailwind.config.js       # Tailwind configuration
│   └── postcss.config.js        # PostCSS with Tailwind plugin
│
└── README.md                    # This file
```

## API Endpoints

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info (requires authentication)

### Conversations
- `POST /conversations` - Create new conversation
- `GET /conversations` - List all user conversations
- `GET /conversations/{id}` - Get conversation with messages
- `PATCH /conversations/{id}` - Update conversation title
- `DELETE /conversations/{id}` - Delete conversation

### Chat
- `POST /chat` - Send message and stream AI response (requires authentication)

## Usage

### 1. Register a New Account
- Open http://localhost:5173
- Click "Register" tab
- Enter username, email, and password
- Click "Create Account"

### 2. Start Chatting
- After registration, you'll be redirected to the chat interface
- Type your message in the input field
- Press Enter or click Send
- Watch the AI response stream in real-time

### 3. Manage Conversations
- View all conversations in the left sidebar
- Click "New Chat" to start a new conversation
- Click on any conversation to view its history
- Hover over a conversation and click the trash icon to delete it

## Development

### Backend Development

The backend uses FastAPI with auto-reload enabled:

```bash
cd backend
source venv/bin/activate
python main.py
```

Changes to Python files will automatically reload the server.

### Frontend Development

The frontend uses Vite with Hot Module Replacement (HMR):

```bash
cd frontend
npm run dev
```

Changes to React components will update instantly in the browser.

### Database Migrations

The database schema is automatically created on server startup. For production, consider using Alembic for migrations:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini and create migrations
```

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Restrict CORS origins in `main.py` (currently set to `["*"]`)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Set up proper logging and monitoring
- [ ] Implement rate limiting
- [ ] Add input validation and sanitization
- [ ] Review and update security headers

### Deployment Options
- **Backend**: Deploy to Railway, Render, AWS, or Google Cloud
- **Frontend**: Deploy to Vercel, Netlify, or Cloudflare Pages
- **Database**: Use managed PostgreSQL (e.g., Supabase, Neon, AWS RDS)

## Troubleshooting

### Backend Issues

**"No such table: users" error**
- The database tables are auto-created on startup. Ensure the server starts successfully.

**"Google API Key not configured" error**
- Make sure you've created a `.env` file in the `backend` directory
- Verify `GOOGLE_API_KEY` is set correctly

**Port 8002 already in use**
- Change the port in `main.py` (line 290): `uvicorn.run("main:app", host="0.0.0.0", port=YOUR_PORT, reload=True)`
- Update the frontend API URL in `ChatInterface.jsx` accordingly

### Frontend Issues

**"Failed to fetch" error**
- Ensure the backend is running on http://localhost:8002
- Check browser console for CORS errors
- Verify the API URL in `ChatInterface.jsx` matches your backend port

**TailwindCSS not working**
- Ensure `@tailwindcss/postcss` is installed: `npm install @tailwindcss/postcss`
- Check `postcss.config.js` is configured correctly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Google Gemini](https://deepmind.google/technologies/gemini/)
- Orchestrated with [LangChain](https://www.langchain.com/)
- UI built with [React](https://react.dev/) and [TailwindCSS](https://tailwindcss.com/)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Made with ❤️ by the SmargeAI Team**
