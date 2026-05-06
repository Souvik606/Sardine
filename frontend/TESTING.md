# Testing Guide for SARDS Frontend Editor

## Prerequisites

1. **Backend API Running**: The SARDS backend must be running and accessible
2. **Node.js & pnpm**: Installed as per main README
3. **Browser**: Modern browser with JavaScript enabled

## Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env.local
```

Update `NEXT_PUBLIC_API_URL` if your backend runs on a different address:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Install Dependencies

```bash
pnpm install
```

This will install all dependencies including Monaco Editor.

### 3. Start Development Server

```bash
pnpm dev
```

The application will be available at `http://localhost:3000`

## Testing Scenarios

### Test 1: Basic Editor Loading
1. Navigate to `http://localhost:3000/editor`
2. **Expected**: Monaco Editor appears with dark theme
3. **Verify**: Editor is responsive and ready for input

### Test 2: Writing Code
1. Click in the editor area
2. Type some test code (e.g., `print("Hello, SARDS!")`)
3. **Expected**: Code appears in editor with proper syntax highlighting
4. **Verify**: Line numbers are visible on the left

### Test 3: Code Execution (Requires Working Backend)
1. Write some valid Sardine code
2. Click the "Run" button
3. **Expected**: Loading indicator appears temporarily
4. **Expected**: Output appears in the right panel
5. **Verify**: Either execution result or error message is displayed

### Test 4: Error Handling
1. Write invalid Sardine code
2. Click "Run"
3. **Expected**: Error message appears in output panel
4. **Verify**: Error is clearly marked in red

### Test 5: Backend Connection Error
1. Stop the backend API server
2. Click "Run" on any code
3. **Expected**: Error message like "Cannot connect to API at http://localhost:8000"
4. **Verify**: User is informed how to fix the issue

### Test 6: Clear Button
1. Write some code
2. Click the "Clear" button
3. **Expected**: Editor is cleared
4. **Expected**: Output panel is reset
5. **Verify**: Both code and results are empty

### Test 7: Responsive Design
1. Open editor on mobile device or use browser dev tools
2. Resize window to mobile size
3. **Expected**: Interface adapts responsively
4. **Verify**: Buttons are still accessible and clickable

### Test 8: Long-Running Code (Timeout Test)
1. Write code that takes longer than 30 seconds
2. Click "Run"
3. **Expected**: Timeout error appears after 30 seconds
4. **Verify**: Clear error message about timeout

## Manual Testing Checklist

- [ ] Editor loads without JavaScript errors
- [ ] Syntax highlighting works for code
- [ ] Can type and edit code
- [ ] Can clear code with Clear button
- [ ] Run button executes code and shows output
- [ ] Error messages are displayed clearly
- [ ] Backend connection errors are handled gracefully
- [ ] UI is responsive on mobile
- [ ] No console errors in browser dev tools

## Automated Testing (Future)

When ready, consider adding:
- Jest unit tests for EditorContainer component
- End-to-end tests with Playwright or Cypress
- API integration tests with mock backend

## Troubleshooting

### Monaco Editor not rendering
```bash
# Clear cache and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
pnpm dev
```

### API connection errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

### Build errors
```bash
# Clean build
pnpm build --no-cache
```

## Browser DevTools

Use browser DevTools to:
- Check console for JavaScript errors
- Monitor Network tab for API requests
- Verify API responses and status codes
- Test performance in Performance tab

## Performance Tips

- Monaco Editor lazy-loads language definitions
- Code execution is handled server-side
- Frontend only sends code to backend via HTTP

## Next Steps After Testing

1. Add unit tests for components
2. Add integration tests with mock API
3. Implement localStorage for code persistence
4. Add keyboard shortcuts (Ctrl+Enter to run, etc.)
5. Add code sharing/URL features
