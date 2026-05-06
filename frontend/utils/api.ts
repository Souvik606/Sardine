const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CodeExecutionRequest {
  code: string;
}

interface CodeExecutionResponse {
  output: string;
  error?: string;
}

/**
 * Execute Sardine code via the backend API
 * @param code - The Sardine code to execute
 * @returns Promise with execution output and any errors
 */
export const executeCode = async (
  code: string
): Promise<CodeExecutionResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code } as CodeExecutionRequest),
    });

    if (!response.ok) {
      if (response.status === 400) {
        return {
          output: "",
          error: "Invalid code syntax",
        };
      }
      if (response.status === 500) {
        return {
          output: "",
          error: "Server error - please try again later",
        };
      }
      const errorData = await response.json().catch(() => ({}));
      return {
        output: "",
        error: errorData.message || `HTTP ${response.status}`,
      };
    }

    const data: CodeExecutionResponse = await response.json();
    return {
      output: data.output || "",
      error: data.error,
    };
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return {
        output: "",
        error: `Cannot connect to API at ${API_BASE_URL}. Make sure the backend is running.`,
      };
    }
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    return {
      output: "",
      error: errorMessage,
    };
  }
};

/**
 * Get code execution status (for future async execution support)
 * @param executionId - The ID of the execution
 * @returns Promise with execution status and result
 */
export const getExecutionStatus = async (executionId: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/executions/${executionId}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    throw error;
  }
};
