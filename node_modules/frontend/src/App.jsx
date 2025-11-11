import { useMemo, useState } from "react";
import ChatBox from "./components/ChatBox.jsx";
import PlotView from "./components/PlotView.jsx";
import { sendPrompt } from "./services/api.js";

function inferChartConfig(data) {
  if (!Array.isArray(data) || data.length === 0) {
    return { type: "line", xKey: "__index", yKey: "__index" };
  }

  const sample = data[0];
  const numericKeys = Object.keys(sample).filter((key) => typeof sample[key] === "number");
  const stringKeys = Object.keys(sample).filter((key) => typeof sample[key] === "string" && key !== "__index");

  if (sample.column !== undefined && numericKeys.includes("count")) {
    return { type: "bar", xKey: "column", yKey: "count" };
  }

  if (numericKeys.includes("count") && stringKeys.length) {
    const xKey = stringKeys[0];
    const type = /date|time/i.test(xKey) ? "area" : "bar";
    return { type, xKey, yKey: "count" };
  }

  const yKey = numericKeys.find((key) => key !== "__index") ?? numericKeys[0] ?? "__index";
  const xKey = stringKeys[0] ?? "__index";
  const type = /date|time/i.test(xKey) ? "area" : "line";

  return { type, xKey, yKey };
}

function preparePlot(name, data) {
  const normalized = Array.isArray(data)
    ? data.map((entry, index) => ({ __index: index + 1, ...entry }))
    : [];

  return {
    name,
    data: normalized,
    config: inferChartConfig(normalized),
  };
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [plots, setPlots] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePromptSubmit = async (value, resetInput) => {
    const prompt = value.trim();
    if (!prompt) {
      return;
    }

    setError(null);
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);

    try {
      const response = await sendPrompt(prompt);
      resetInput();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Plot ready: ${response.plot_name}` },
      ]);

      setPlots((prev) => [...prev, preparePlot(response.plot_name, response.processed_data)]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const hasPlots = useMemo(() => plots.length > 0, [plots]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Talk Plot Dashboard</h1>
        <p>Send a prompt to analyze the underlying dataset and visualize the results.</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="app-main">
        <section className="chat-panel">
          <div className="chat-log">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
                <strong>{message.role === "user" ? "You" : "System"}</strong>
                <div>{message.content}</div>
              </div>
            ))}
            {isLoading && <div className="chat-message system">Processing...</div>}
          </div>
          <ChatBox onSubmit={handlePromptSubmit} disabled={isLoading} />
        </section>

        <section className="plots-grid">
          {hasPlots ? (
            plots.map((plot, index) => <PlotView key={`${plot.name}-${index}`} plot={plot} />)
          ) : (
            <div className="plot-card">
              <h2>Visualizations</h2>
              <div className="plot-placeholder">Your charts will appear here after processing.</div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
