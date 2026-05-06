# 🚀 Quick Start Guide - Full Stack

Get the entire SARDS ecosystem running in 2 minutes!

## Prerequisites

- Python 3.10+ installed
- Node.js 20+ installed
- pnpm installed (`npm install -g pnpm`)

## Step 1: Install Backend Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask and CORS support for the API server.

## Step 2: Start the Backend API

```bash
python api_server.py
```

You should see:
```
Starting SARDS Backend API Server...
Server running on http://localhost:8000
```

✅ **Backend is running!** Keep this terminal open.

## Step 3: Install Frontend Dependencies (New Terminal)

```bash
cd frontend
pnpm install
```

## Step 4: Configure Frontend Environment

```bash
cp .env.example .env.local
```

The default `NEXT_PUBLIC_API_URL=http://localhost:8000` should work. Leave it as is.

## Step 5: Start Frontend Development Server

```bash
pnpm dev
```

You should see:
```
  ▲ Next.js 15.1.7
  - Ready in 1.23s
  - Local: http://localhost:3000
```

## Step 6: Open the Web Editor

Open your browser to: **http://localhost:3000/editor**

You should see the Sardine code editor with:
- Code editor on the left (Monaco Editor)
- Output panel on the right
- Run and Clear buttons in the toolbar

## Test It Out! 🎉

Try writing some Sardine code:

```sardine
x = 5
y = 10
show x + y
```

Click the **Run** button (or press **Ctrl+Enter**) and you should see `15` in the output!

## Available Files

| File | Purpose |
|------|---------|
| **api_server.py** | Backend REST API server |
| **requirements.txt** | Backend Python dependencies |
| **BACKEND_API.md** | Backend API documentation |
| **frontend/README.md** | Frontend documentation |
| **frontend/TESTING.md** | Frontend testing guide |
| **frontend/API_INTEGRATION.md** | Frontend-backend integration details |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Enter (or Cmd+Enter on Mac) | Run code |
| Ctrl+A | Select all code |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |

## Troubleshooting

### "Cannot connect to API" error in frontend
- Check that backend is running on port 8000
- Run: `curl http://localhost:8000/health` to verify

### Port already in use
If port 8000 or 3000 is already in use:
- **Port 8000**: Edit `api_server.py` and change the port number
- **Port 3000**: Frontend will prompt to use a different port

### Module not found errors
- Backend: Run `pip install -r requirements.txt`
- Frontend: Run `pnpm install`

### Frontend doesn't start
- Make sure you're in the `frontend` directory
- Run `pnpm install` to ensure dependencies are installed

## Next Steps

- 📖 Read `BACKEND_API.md` for API endpoints and curl examples
- 🧪 Follow `frontend/TESTING.md` for testing procedures
- 🔧 Check `frontend/API_INTEGRATION.md` for integration details

## Useful Commands

### Backend
```bash
# Start API server
python api_server.py

# Test health check
curl http://localhost:8000/health

# Execute code
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "show 42"}'
```

### Frontend
```bash
cd frontend

# Start development
pnpm dev

# Run linter
pnpm lint

# Format code
pnpm format

# Build for production
pnpm build
```

## Architecture Overview

```
User Browser (http://localhost:3000)
        ↓
   Next.js Frontend
   Monaco Editor UI
        ↓
REST API Call (http://localhost:8000/api/execute)
        ↓
Flask Backend API
Sardine Interpreter
        ↓
Code Execution Result
        ↓
Output Display in Editor
```

## What You Can Do

✅ Write Sardine code in the web editor
✅ Execute code with one click
✅ See results in real-time
✅ Clear and rewrite code
✅ Code automatically saves to browser
✅ Use keyboard shortcuts for quick execution

## Production Deployment

For production use, see:
- `BACKEND_API.md` - Gunicorn, Docker, Nginx setup
- `frontend/README.md` - Production build instructions

---

**That's it! You're ready to start coding in Sardine! 🎉**

For detailed documentation:
- Backend: See `BACKEND_API.md`
- Frontend: See `frontend/README.md`
- Integration: See `frontend/API_INTEGRATION.md`
