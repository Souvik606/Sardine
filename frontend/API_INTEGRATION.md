# SARDS Backend API Integration Guide

This document describes how the frontend integrates with the SARDS backend API.

## API Endpoint Specification

### Code Execution Endpoint

**Endpoint:** `POST /api/execute`

**Request:**
```json
{
  "code": "string (the Sardine code to execute)"
}
```

**Successful Response (200):**
```json
{
  "output": "string (the execution output/result)",
  "error": null
}
```

**Error Response (400, 500):**
```json
{
  "output": "",
  "error": "string (error message)"
}
```

### Execution Status Endpoint (Future)

**Endpoint:** `GET /api/executions/{executionId}`

For async execution tracking (planned enhancement).

## Expected Behavior

### Successful Execution
1. User writes Sardine code in the editor
2. User clicks "Run" button or presses Ctrl+Enter
3. Frontend sends code to `/api/execute`
4. Backend processes the code
5. Backend returns output
6. Frontend displays output in the output panel

### Error Handling

The frontend handles these error scenarios:

| Scenario | Status | Frontend Behavior |
|----------|--------|-------------------|
| Invalid Sardine syntax | 400 | Show "Invalid code syntax" |
| Runtime error | 500 | Show server error message |
| Network unavailable | N/A | Show "Cannot connect to API" |
| Request timeout | N/A | Show "Request timeout" |
| Backend not running | N/A | Helpful connection guide |

## Frontend Code Flow

```
User Input (Monaco Editor)
        ↓
Click "Run" or Ctrl+Enter
        ↓
EditorContainer.handleRun()
        ↓
executeCode(code) in utils/api.ts
        ↓
axios POST /api/execute
        ↓
Handle Response / Error
        ↓
Display Result in Output Panel
```

## Configuration

### Environment Variables

The frontend uses `NEXT_PUBLIC_API_URL` to determine the backend location:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This variable is exposed to the browser (hence `NEXT_PUBLIC_` prefix).

### Timeout Settings

- **Request Timeout:** 30 seconds (configured in `utils/api.ts`)
- **Backend Timeout:** Depends on backend configuration (communicate with backend team)

## Data Persistence

### Client-Side Storage

Code is automatically saved to browser's localStorage:
- **Storage Key:** `sards_editor_code`
- **Persistence:** Survives page refresh
- **Clear:** Happens when user clicks "Clear" button

No server-side persistence is implemented; consider this for future enhancements.

## Future Enhancements

### Planned Features
1. **Async Execution**: Long-running code with status polling
2. **Code Sharing**: Generate shareable links for code snippets
3. **Execution History**: Track previous executions
4. **Code Formatting**: Format code with backend formatter
5. **Syntax Validation**: Real-time validation as user types
6. **Multiple Language Support**: Support more languages than Python

### Recommended Backend Features
1. **Health Check Endpoint:** `GET /health` for connectivity checks
2. **Syntax Validator:** `POST /api/validate` for real-time validation
3. **Code Formatter:** `POST /api/format` for code formatting
4. **Execution Timeout:** Configurable timeout for long-running code
5. **Rate Limiting:** Prevent abuse with rate limiting
6. **Authentication:** Optional authentication for production

## Testing the API

### Using curl (if backend is running)

```bash
# Test basic execution
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, SARDS!\")"}'

# Test error handling
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "invalid syntax @#$"}'

# Test health check (recommended)
curl http://localhost:8000/health
```

### Using the Frontend UI

1. Navigate to `http://localhost:3000/editor`
2. Write code and click "Run"
3. Check browser Network tab in DevTools
4. View API request and response

## Debugging

### Check API Connectivity
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Run" in editor
4. Look for POST request to `/api/execute`
5. Check response status and body

### Common Issues

**"Cannot connect to API"**
- Backend is not running
- Backend is on wrong port/URL
- CORS issues (backend needs to allow frontend origin)

**Code executes but no output**
- Check if backend is returning `output` field
- Check if backend is returning `error: null` for success

**Timeout errors**
- Code execution is taking too long
- Increase timeout in `utils/api.ts` if needed
- Optimize backend code execution

## Backend Requirements

To integrate with this frontend, your backend must:

1. ✅ Accept POST requests at `/api/execute`
2. ✅ Accept JSON with `code` field
3. ✅ Return JSON with `output` and optional `error` fields
4. ✅ Set appropriate HTTP status codes (200 for success, 400/500 for errors)
5. ⚠️ Handle CORS (allow requests from frontend origin)
6. ✅ Validate input code
7. ✅ Execute code safely (sandboxing recommended)
8. ✅ Return results within reasonable time (recommend <30 seconds)

### Example Backend Response

**Success:**
```json
{
  "output": "Hello, SARDS!\n42\nTrue",
  "error": null
}
```

**Error:**
```json
{
  "output": "",
  "error": "SyntaxError: invalid syntax at line 1"
}
```

## CORS Configuration

If your frontend and backend are on different origins, the backend must allow CORS:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

## Security Considerations

1. **Input Validation:** Backend should validate code syntax
2. **Sandboxing:** Execute code in isolated environment
3. **Rate Limiting:** Prevent DOS attacks
4. **Timeout:** Kill long-running processes
5. **Output Sanitization:** Clean output before sending to frontend
6. **Error Messages:** Don't expose sensitive system info in errors

## Support

For issues or questions about the frontend integration:
1. Check this guide
2. Review `TESTING.md` for testing procedures
3. Check browser console for error messages
4. Review network requests in DevTools
