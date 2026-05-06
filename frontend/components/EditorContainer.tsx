"use client";

import React, { useState, useCallback, useEffect } from "react";
import Editor, { OnChange } from "@monaco-editor/react";
import { Play, Trash, Loader, Copy, Check } from "lucide-react";
import { executeCode } from "@/utils/api";

interface ExecutionResult {
  output: string;
  error?: string;
  status: "success" | "error" | "pending";
}

const STORAGE_KEY = "sards_editor_code";
const COPY_FEEDBACK_DURATION = 2000;

const EditorContainer: React.FC = () => {
  const [code, setCode] = useState<string>("");
  const [result, setResult] = useState<ExecutionResult>({
    output: "",
    status: "pending",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Load code from localStorage on mount
  useEffect(() => {
    const savedCode = localStorage.getItem(STORAGE_KEY);
    if (savedCode) {
      setCode(savedCode);
    }
  }, []);

  // Save code to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, code);
  }, [code]);

  const handleCodeChange: OnChange = (value) => {
    setCode(value || "");
  };

  const handleRun = useCallback(async () => {
    if (!code.trim()) {
      setResult({
        output: "// Please write some code first",
        status: "error",
      });
      return;
    }

    setIsLoading(true);
    setResult({ output: "Executing...", status: "pending" });

    try {
      const response = await executeCode(code);
      setResult({
        output: response.output,
        error: response.error,
        status: response.error ? "error" : "success",
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      setResult({
        output: errorMessage,
        error: errorMessage,
        status: "error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [code]);

  const handleClear = useCallback(() => {
    setCode("");
    setResult({ output: "", status: "pending" });
  }, []);

  const handleCopyOutput = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(result.output);
      setCopied(true);
      setTimeout(() => setCopied(false), COPY_FEEDBACK_DURATION);
    } catch (error) {
      console.error("Failed to copy output:", error);
    }
  }, [result.output]);

  // Keyboard shortcuts: Ctrl+Enter or Cmd+Enter to run
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleRun();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleRun]);

  return (
    <div className="wrapper w-3/4 overflow-hidden rounded-lg border border-zinc-700 bg-gray-850 shadow-lg transition-all focus-within:w-full">
      <div className="flex h-12 items-center justify-between border-b border-zinc-700 bg-zinc-800 px-4">
        <div className="text-lg font-semibold text-white">Playground</div>
        <div className="flex space-x-4">
          <button
            onClick={handleRun}
            disabled={isLoading}
            title="Run code (Ctrl+Enter)"
            className="flex items-center gap-2 rounded-full border border-teal-400 px-2 py-2 font-medium text-teal-400 transition-all hover:bg-teal-400 hover:text-zinc-800 disabled:opacity-50 disabled:hover:bg-transparent md:px-8 md:py-1"
          >
            {isLoading ? (
              <Loader className="inline size-3 animate-spin" />
            ) : (
              <Play className="inline size-3" fill="currentColor" />
            )}
            <span className="hidden md:inline">{isLoading ? "Running..." : "Run"}</span>
          </button>
          <button
            onClick={handleClear}
            disabled={isLoading}
            title="Clear code"
            className="flex items-center gap-2 rounded-full border border-red-700 px-2 py-2 font-medium text-red-700 transition-all hover:bg-red-700 hover:text-zinc-800 disabled:opacity-50 disabled:hover:bg-transparent md:px-8 md:py-1"
          >
            <Trash className="inline size-3" fill="currentColor" />
            <span className="hidden md:inline">Clear</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap">
        <div className="w-1/2 bg-zinc-900">
          <Editor
            height="400px"
            defaultLanguage="python"
            language="python"
            value={code}
            onChange={handleCodeChange}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              fontFamily: 'Fira Code, monospace',
              tabSize: 2,
              wordWrap: "on",
              automaticLayout: true,
              scrollBeyondLastLine: false,
            }}
          />
        </div>
        <div
          className={`font-code flex grow flex-col overflow-auto bg-slate-950/20 p-4 ${
            result.status === "error" ? "border-l-4 border-red-500" : ""
          }`}
        >
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm text-gray-400">
              <span className="font-medium text-yellow-100">$</span> Output
            </div>
            {result.output && (
              <button
                onClick={handleCopyOutput}
                title="Copy output"
                className="text-xs text-gray-500 transition-colors hover:text-gray-300"
              >
                {copied ? (
                  <Check className="inline size-3" />
                ) : (
                  <Copy className="inline size-3" />
                )}
              </button>
            )}
          </div>
          <pre className="whitespace-pre-wrap break-words font-mono text-sm text-white">
            {result.output || "// Run your code to see output here"}
          </pre>
          {result.error && (
            <div className="mt-2 border-t border-red-500 pt-2 text-sm text-red-400">
              <strong>Error:</strong> {result.error}
            </div>
          )}
        </div>
      </div>
      
      <div className="border-t border-zinc-700 bg-zinc-800 px-4 py-2 text-xs text-gray-400">
        <span className="text-yellow-100">💡 Tip:</span> Use Ctrl+Enter (or Cmd+Enter on Mac) to quickly run your code. Your code is automatically saved.
      </div>
    </div>
  );
};

export default EditorContainer;
