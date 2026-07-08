import type { Transaction } from "../api";

interface Props {
  transactions: Transaction[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function FlaggedFeed({ transactions, selectedId, onSelect }: Props) {
  return (
    <div className="flagged-feed">
      <h2>Flagged Transactions</h2>
      <ul>
        {transactions.map((t) => (
          <li
            key={t.id}
            className={t.id === selectedId ? "selected" : ""}
            onClick={() => onSelect(t.id)}
          >
            <div className="row">
              <span className="account">{t.account_id}</span>
              <span className="score">{(t.fraud_score ?? 0).toFixed(3)}</span>
            </div>
            <div className="row">
              <span className="amount">${t.amount.toFixed(2)}</span>
              <span className="timestamp">{new Date(t.timestamp).toLocaleString()}</span>
            </div>
          </li>
        ))}
        {transactions.length === 0 && <li className="empty">No flagged transactions yet.</li>}
      </ul>
    </div>
  );
}
