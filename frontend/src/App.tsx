import { useEffect, useState } from "react";
import { fetchFlaggedTransactions, type Transaction } from "./api";
import { FlaggedFeed } from "./components/FlaggedFeed";
import { InvestigationPanel } from "./components/InvestigationPanel";

export default function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetchFlaggedTransactions().then(setTransactions).catch(console.error);
  }, []);

  return (
    <div className="app">
      <header>
        <h1>FinGuard</h1>
      </header>
      <main>
        <FlaggedFeed
          transactions={transactions}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <InvestigationPanel transactionId={selectedId} />
      </main>
    </div>
  );
}
