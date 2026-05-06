# SARDS Development Guide

## Project Structure Overview

```
SARDS/
├── sards/                          # Core Sardine language implementation
│   ├── core/                       # Lexer, Parser, Interpreter
│   ├── ast_nodes/                  # AST node definitions
│   ├── data_types/                 # Sardine data types
│   ├── oops_types/                 # Object-oriented features
│   ├── user_functions/             # User-defined functions
│   └── shell.py                    # Interactive REPL
│
├── frontend/                       # Next.js web editor
│   ├── app/                        # Next.js app directory
│   ├── components/                 # React components
│   ├── utils/                      # Utilities (API service)
│   └── styles/                     # CSS
│
├── api_server.py                   # Flask REST API
├── requirements.txt                # Backend dependencies
├── README.md                       # Project README
└── docs/                           # Documentation
```

## Architecture

### Three-Layer Design

1. **Presentation Layer** (frontend/)
   - React 19 with Next.js
   - Monaco Editor for code editing
   - HTTP client (Axios)

2. **Application Layer** (api_server.py)
   - Flask REST API
   - Request routing
   - Error handling

3. **Core Layer** (sards/)
   - Lexer (tokenization)
   - Parser (syntax analysis)
   - Interpreter (execution)

## Development Workflow

### Frontend Development

```bash
cd frontend
pnpm dev        # Start dev server on :3000
pnpm lint       # Check code quality
pnpm format     # Format code
pnpm build      # Production build
```

**Key Files:**
- `components/EditorContainer.tsx` - Main editor component
- `utils/api.ts` - API communication
- `app/(editor)/editor/page.tsx` - Editor page

### Backend Development

```bash
python api_server.py        # Start API server on :8000
```

**Key Files:**
- `api_server.py` - REST API implementation
- `sards/shell.py` - Sardine interpreter entry point

### Sardine Language Development

```bash
python -m sards.shell      # Start interactive REPL
# Or edit sards/samples/main.sad and select File Input mode
```

**Key Files:**
- `sards/core/lexer.py` - Tokenization
- `sards/core/parser.py` - Parsing
- `sards/core/interpreter.py` - Execution
- `sards/ast_nodes/` - AST node types

## Adding New Features

### Adding a Built-in Function

1. **In `sards/`** (backend):
   Define the function in `core/interpreter.py` or create a new data type

2. **In `api_server.py`**:
   Add it to `global_symbol_table`:
   ```python
   global_symbol_table.set("my_func", BuiltInFunction.my_func)
   ```

3. **In frontend** (optional):
   Update syntax highlighting in `utils/syntax-highlight.ts`

4. **Test**:
   - Test via API: `curl -X POST http://localhost:8000/api/execute`
   - Test via frontend: Run code in editor
   - Test via REPL: `python -m sards.shell`

### Adding a Language Feature

1. **Update Lexer** (`sards/core/lexer.py`):
   - Add new tokens if needed

2. **Update Parser** (`sards/core/parser.py`):
   - Add parsing logic for new syntax

3. **Create AST Node** (`sards/ast_nodes/`):
   - Define node structure

4. **Update Interpreter** (`sards/core/interpreter.py`):
   - Implement execution logic

5. **Test**:
   - Unit tests in test files
   - Integration test via API/frontend

### Adding Frontend Features

1. **Update EditorContainer** (`frontend/components/EditorContainer.tsx`):
   - Add UI elements
   - Add state management
   - Add event handlers

2. **Update API Service** (`frontend/utils/api.ts`):
   - Add new API calls if needed

3. **Style with Tailwind**:
   - Use Tailwind classes for styling

4. **Test**:
   - Manual testing in browser
   - Check browser console for errors

## Useful Commands

### Frontend
```bash
cd frontend

# Development
pnpm dev                  # Start dev server
pnpm lint                 # Run ESLint
pnpm format               # Format with Prettier

# Building
pnpm build                # Production build
pnpm start                # Start production server

# Dependency management
pnpm add <package>        # Add dependency
pnpm add --save-dev <pkg> # Add dev dependency
pnpm remove <package>     # Remove dependency
pnpm update               # Update all packages
```

### Backend
```bash
# API server
python api_server.py                # Start API

# Sardine interpreter
python -m sards.shell               # Interactive shell
python -c "from sards import *"     # Import in Python

# Package management
pip install -r requirements.txt     # Install dependencies
pip freeze > requirements.txt       # Save dependencies
pip list                            # List installed packages
```

### Git
```bash
git status                          # Check status
git add .                           # Stage changes
git commit -m "message"             # Commit
git push                            # Push to remote
git pull                            # Pull from remote
```

## Debugging

### Frontend Debugging

1. **Browser DevTools**:
   - F12 or Right-click → Inspect
   - Console tab for errors
   - Network tab for API calls
   - React DevTools extension

2. **VS Code Debugging**:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Next.js: debug",
         "type": "node",
         "request": "launch",
         "program": "${workspaceFolder}/frontend/node_modules/.bin/next",
         "args": ["dev"],
         "cwd": "${workspaceFolder}/frontend"
       }
     ]
   }
   ```

### Backend Debugging

1. **Print statements**:
   ```python
   print(f"Debug: {variable}")  # Check api_server.py output
   ```

2. **Flask debug mode** (in api_server.py):
   ```python
   app.run(debug=True)  # Automatic reload on changes
   ```

3. **Python debugger**:
   ```python
   import pdb; pdb.set_trace()  # Set breakpoint
   ```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Simple execution
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "show 1"}'

# With error
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "bad syntax @#$"}'

# With variables
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "x = 5\nshow x"}'
```

## Performance Optimization Tips

### Frontend
- Use React.memo for expensive components
- Lazy load Monaco Editor
- Optimize bundle size
- Cache API responses

### Backend
- Add execution timeout to prevent hangs
- Cache compiled code if possible
- Use connection pooling
- Monitor memory usage

### General
- Profile code with dev tools
- Use CDN for static assets
- Enable compression
- Monitor latency

## Security Best Practices

### Frontend
- ✅ Already: No sensitive data in localStorage
- ⚠️ TODO: Add rate limiting on frontend
- ⚠️ TODO: Validate input before sending

### Backend
- ⚠️ TODO: Sandbox code execution
- ⚠️ TODO: Add timeout for long executions
- ⚠️ TODO: Implement API authentication
- ⚠️ TODO: Add rate limiting
- ⚠️ TODO: Sanitize error messages

### Deployment
- Use HTTPS in production
- Set CORS appropriately
- Run behind reverse proxy (Nginx)
- Use container (Docker)
- Regular security updates

## Testing Strategy

### Unit Tests
```bash
# Frontend
cd frontend
pnpm test              # (Not yet configured)

# Backend
python -m pytest       # (Add pytest)
```

### Integration Tests
- Test API endpoints with curl
- Test full flow frontend → backend

### E2E Tests
- Use Playwright or Cypress
- Test complete user workflows

### Manual Testing
See `frontend/TESTING.md` for 8 manual test scenarios

## Documentation

### Adding Documentation
1. Create `.md` file in project root or `docs/`
2. Link from README.md
3. Keep examples current
4. Update when features change

### Key Documentation Files
- `README.md` - Project overview
- `QUICKSTART.md` - Quick setup
- `BACKEND_API.md` - API documentation
- `frontend/README.md` - Frontend docs
- `frontend/TESTING.md` - Testing guide
- `frontend/API_INTEGRATION.md` - Integration guide
- `docs/grammar_rules.md` - Language grammar

## Contribution Workflow

1. **Create a branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**:
   - Write code
   - Add tests
   - Update docs

3. **Test locally**:
   ```bash
   # Frontend
   cd frontend && pnpm lint && pnpm build
   
   # Backend
   python api_server.py  # Ensure it starts
   ```

4. **Commit with message**:
   ```bash
   git commit -m "feat: add my feature"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

## Useful Resources

### Sardine
- `docs/grammar_rules.md` - Language specification
- `sards/samples/` - Example code
- `sards/core/` - Core implementation

### Frontend
- [Next.js Docs](https://nextjs.org/)
- [React Docs](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Monaco Editor](https://github.com/microsoft/monaco-editor)

### Backend
- [Flask Docs](https://flask.palletsprojects.com/)
- [Flask-CORS](https://flask-cors.readthedocs.io/)

## Troubleshooting Development

### Port already in use
```bash
# Find process on port
lsof -i :8000          # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>          # Mac/Linux
taskkill /PID <PID> /F # Windows
```

### Module import errors
```bash
# Frontend
cd frontend && pnpm install

# Backend
pip install -r requirements.txt
```

### TypeScript errors
```bash
cd frontend
npx tsc --noEmit      # Check types without building
```

### API not responding
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", "message": "SARDS API is running"}
```

## Next Development Priorities

1. **Testing**
   - Add unit tests
   - Add E2E tests
   - Increase coverage to 80%+

2. **Performance**
   - Add execution timeout
   - Implement caching
   - Optimize bundle size

3. **Features**
   - Code sharing
   - Execution history
   - Real-time syntax validation
   - Code formatting

4. **Production**
   - Docker setup
   - CI/CD pipeline
   - Monitoring/logging
   - Database backend

---

*Last Updated: 2026-05-04*
*Questions? Check the relevant .md file in the project root*
