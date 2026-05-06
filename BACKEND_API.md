# SARDS Backend API Server

A Flask-based REST API that exposes the Sardine interpreter for remote code execution.

## Quick Start

### 1. Install Dependencies

```bash
# From the project root directory
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python api_server.py
```

The server will start on `http://localhost:8000`

You should see:
```
Starting SARDS Backend API Server...
Server running on http://localhost:8000
Press Ctrl+C to stop the server
```

## API Endpoints

### Health Check
```
GET /health
```

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "SARDS API is running"
}
```

**Status Code:** 200

### Execute Code
```
POST /api/execute
```

Execute Sardine code and get the result.

**Request:**
```json
{
  "code": "show 1 + 2"
}
```

**Successful Response (200):**
```json
{
  "output": "3",
  "error": null
}
```

**Error Response (200):**
```json
{
  "output": "",
  "error": "SyntaxError: Invalid token at line 1"
}
```

**Bad Request (400):**
```json
{
  "output": "",
  "error": "Missing 'code' field in request"
}
```

### API Info
```
GET /
```

Get information about the API and available endpoints.

**Response:**
```json
{
  "name": "SARDS Backend API",
  "version": "1.0.0",
  "description": "REST API for executing Sardine code",
  "endpoints": {
    "POST /api/execute": "Execute Sardine code",
    "GET /health": "Health check",
    "GET /": "API information"
  }
}
```

## Testing with curl

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Execute Simple Code
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "show 1 + 2"}'
```

### Execute with Variables
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "x = 5\ny = 10\nshow x + y"}'
```

### Test Error Handling
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "invalid syntax @#$"}'
```

## Configuration

### Port
Default: 8000

To change, edit `api_server.py` line at the bottom:
```python
app.run(host="0.0.0.0", port=YOUR_PORT, debug=False)
```

### Debug Mode
The API runs with `debug=False` for production safety. To enable debug mode:
```python
app.run(host="0.0.0.0", port=8000, debug=True)
```

### Host
Default: 0.0.0.0 (accessible from any machine)

To restrict to localhost only:
```python
app.run(host="127.0.0.1", port=8000, debug=False)
```

## CORS (Cross-Origin Resource Sharing)

CORS is enabled for all origins, allowing the frontend to make requests from any domain. This is configured in the code:

```python
CORS(app)  # Allows requests from any origin
```

To restrict CORS to specific origins:
```python
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
```

## Error Handling

### Timeout
Currently no execution timeout is set. To add a timeout, you can modify the `execute_sardine_code` function with signal handlers (on Unix/Linux) or use a timeout library.

### Large Output
Output size is not limited. For production, consider adding limits to prevent memory issues.

### Security
⚠️ **Important**: This API does NOT sandbox code execution. Untrusted code can:
- Access the file system
- Run arbitrary Python commands (via Sardine's interpreter)
- Consume system resources

For production use, consider:
1. Running the API in a container/sandbox
2. Using a process timeout
3. Limiting code complexity
4. Validating input code before execution
5. Running in a restricted user account

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
Install dependencies: `pip install -r requirements.txt`

### "Port 8000 already in use"
Either:
1. Kill the process using port 8000
2. Change the port in `api_server.py`

### "ModuleNotFoundError: No module named 'sards'"
Make sure you're running from the project root directory where the `sards` package exists.

### Frontend Can't Connect
- Verify API is running: `curl http://localhost:8000/health`
- Check frontend's `NEXT_PUBLIC_API_URL` environment variable
- Ensure CORS is enabled
- Check firewall settings

## Integration with Frontend

The frontend expects the API to be running at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL` environment variable).

When the frontend calls `/api/execute`:
1. Sends POST request with `{"code": "..."}`
2. API executes the code in the Sardine interpreter
3. API returns `{"output": "...", "error": null}` or `{"output": "", "error": "..."}`
4. Frontend displays the output or error

## Advanced Usage

### Running with Gunicorn (Production)
For production deployment, use Gunicorn instead of the Flask development server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 api_server:app
```

### Running with Nginx Reverse Proxy
Example nginx configuration:
```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker Deployment
Example Dockerfile:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "api_server.py"]
```

Build and run:
```bash
docker build -t sards-api .
docker run -p 8000:8000 sards-api
```

## Monitoring

### Access Logs
Flask logs all requests. To enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Execution Metrics
To track execution time and code statistics, you can modify the `execute_sardine_code` function:

```python
import time
start = time.time()
# ... execute code ...
duration = time.time() - start
```

## Performance Notes

- First execution may be slower as Python imports are loaded
- Subsequent requests are faster (imports are cached)
- Complex code may take longer to execute
- Output size affects response time

## Future Enhancements

1. **Timeout Support**: Add execution timeout with signal handlers
2. **Async Execution**: Support long-running code with polling
3. **Code Validation**: Pre-validate syntax without execution
4. **Execution History**: Store execution logs
5. **Code Formatting**: Endpoint to format code
6. **Sandbox**: Restrict file system and resource access
7. **Rate Limiting**: Prevent abuse
8. **Authentication**: Secure endpoints with API keys

## Support

For issues or questions:
1. Check this documentation
2. Review `api_server.py` comments
3. Test with curl commands
4. Check server logs for error messages
5. Review frontend's `API_INTEGRATION.md`
