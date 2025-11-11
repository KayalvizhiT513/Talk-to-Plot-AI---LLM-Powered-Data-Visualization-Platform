import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function sendPrompt(prompt) {
  const trimmed = prompt.trim();
  if (!trimmed) {
    throw new Error("Prompt cannot be empty");
  }

  try {
    const { data } = await axios.post(`${API_BASE_URL}/chat`, { prompt: trimmed });
    return data;
  } catch (error) {
    const message = error.response?.data?.detail ?? error.message ?? "Unknown error";
    throw new Error(message);
  }
}
