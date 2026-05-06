# SARDS Frontend

This is the frontend for the SARDS (Sardine) programming language editor. It's a Next.js 15 application built with TypeScript, Tailwind CSS, and Monaco Editor.

## Features

- **Monaco Code Editor**: Professional code editor with syntax highlighting and intelligent code completion
- **Code Execution**: Execute Sardine code directly from the browser via backend API
- **Real-time Output**: View code execution results and error messages in real-time
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Prerequisites

- **Node.js**: v20 or later (download from [nodejs.org](https://nodejs.org/))
- **pnpm**: v9 or later. Install globally with:
  ```bash
  npm install -g pnpm
  ```
- **SARDS Backend API**: The backend server must be running for code execution (typically at `http://localhost:8000`)

## Getting Started

1. **Install dependencies**:
   ```bash
   pnpm install
   ```

2. **Configure environment variables**:
   Create a `.env.local` file in the frontend directory based on `.env.example`:
   ```bash
   cp .env.example .env.local
   ```
   
   Update the `NEXT_PUBLIC_API_URL` if your backend is running on a different address.

3. **Run the development server**:
   ```bash
   pnpm dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser to see the application in action.

4. **Access the editor**:
   Navigate to [http://localhost:3000/editor](http://localhost:3000/editor) to start writing and executing Sardine code.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | The URL of the SARDS backend API server |

## Project Structure

```
frontend/
├── app/              # Next.js app directory with routes
│   ├── (root)/      # Root route group
│   ├── (editor)/    # Editor route group
│   └── (docs)/      # Documentation route group
├── components/       # Reusable React components
│   ├── EditorContainer.tsx  # Main editor component with Monaco
│   ├── Editor.tsx           # Legacy textarea editor (deprecated)
│   ├── FixedNav.tsx         # Navigation component
│   └── ...
├── utils/           # Utility functions and services
│   ├── api.ts       # API client for backend communication
│   └── syntax-highlight.ts
├── styles/          # Global styles
└── public/          # Static assets
```

## Available Scripts

```bash
# Development
pnpm dev           # Start development server with Turbopack

# Build
pnpm build         # Build for production
pnpm start         # Start production server

# Code Quality
pnpm lint          # Run ESLint
pnpm format        # Format code with Prettier
```

## Architecture

### EditorContainer Component
The main editor component that:
- Integrates Monaco Editor for code editing
- Manages code state
- Handles code execution via API
- Displays execution results and errors

### API Service (`utils/api.ts`)
Provides functions for:
- `executeCode(code)` - Execute Sardine code on the backend
- `getExecutionStatus(executionId)` - Get status of async executions (future)

### Error Handling
The application gracefully handles:
- Network errors when backend is unavailable
- Syntax errors in user code
- Request timeouts for long-running executions
- Server errors with helpful user messages

## Development Tips

- The Monaco Editor is configured for dark mode with a comfortable font size and tab width of 2
- Code execution is limited by the backend API's timeout settings
- Check the browser console for detailed error messages during development

## Production Build

To build the project for production:

```bash
pnpm build
```

To start the production server:

```bash
pnpm start
```

## Troubleshooting

### "Cannot connect to API" error
- Ensure the SARDS backend API is running at the configured `NEXT_PUBLIC_API_URL`
- Check network connectivity and firewall settings
- Verify the `NEXT_PUBLIC_API_URL` environment variable is correctly set

### Code execution timeouts
- The backend has a 30-second timeout for code execution
- Complex operations may exceed this limit
- Check the backend logs for more details

### Monaco Editor not loading
- Clear your browser cache and reload
- Ensure all dependencies are installed: `pnpm install`
- Check for console errors in the browser developer tools

