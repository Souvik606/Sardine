import axios, { AxiosError } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CodeExecutionRequest {
  code: string;
}

interface CodeExecutionResponse {
  output: string;
  error?: string;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Execute Sardine code via the backend API
 * @param code - The Sardine code to execute
 * @returns Promise with execution output and any errors
 */
export const executeCode = async (
  code: string
): Promise<CodeExecutionResponse> => {
  try {
    const response = await apiClient.post<CodeExecutionResponse>(
      "/api/execute",
      { code } as CodeExecutionRequest
    );

    return {
      output: response.data.output || "",
      error: response.data.error,
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ message?: string }>;

      // Handle specific error scenarios
      if (axiosError.response?.status === 400) {
        return {
          output: "",
          error: "Invalid code syntax",
        };
      }

      if (axiosError.response?.status === 500) {
        return {
          output: "",
          error: "Server error - please try again later",
        };
      }

      if (axiosError.code === "ECONNABORTED") {
        return {
          output: "",
          error: "Request timeout - code execution took too long",
        };
      }

      if (axiosError.message === "Network Error") {
        return {
          output: "",
          error: `Cannot connect to API at ${API_BASE_URL}. Make sure the backend is running.`,
        };
      }

      return {
        output: "",
        error: axiosError.response?.data?.message || axiosError.message,
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
    const response = await apiClient.get(`/api/executions/${executionId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export default apiClient;
