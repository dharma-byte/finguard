import { useState } from "react";
import { investigate, type InvestigateResponse } from "../api";

interface Props {
  transactionId: string | null;
}

export function InvestigationPanel({ transactionId }: Props) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<InvestigateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!transactionId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await investigate(transactionId, question || undefined);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation failed");
    } finally {
      setLoading(false);
    }
  }

  if (!transactionId) {
    return (
      <div className="investigation-panel">
        <h2>Investigation</h2>
        <p>Select a flagged transaction to investigate.</p>
      </div>
    );
  }

  return (
    <div className="investigation-panel">
      <h2>Investigation: {transactionId}</h2>
      <div className="question-row">
        <input
          type="text"
          placeholder="Ask a question (optional)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button onClick={handleAsk} disabled={loading}>
          {loading ? "Investigating..." : "Investigate"}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result">
          <p className="summary">{result.summary}</p>
          <h3>Cited Cases</h3>
          <ul>
            {result.cited_cases.map((c) => (
              <li key={c.case_id}>
                <span className="case-id">{c.case_id}</span>
                <span className="outcome">{c.outcome}</span>
                <span className="relevance">{c.relevance_score.toFixed(3)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
