export interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  timestamp: string;
  fraud_score: number | null;
  is_flagged: boolean;
  top_shap_features: { feature: string; impact: number }[];
}

export interface CitedCase {
  case_id: string;
  transaction_id: string;
  outcome: string;
  relevance_score: number;
}

export interface InvestigateResponse {
  summary: string;
  cited_cases: CitedCase[];
}

const BASE_URL = "/api";

export async function fetchFlaggedTransactions(): Promise<Transaction[]> {
  const res = await fetch(`${BASE_URL}/transactions/flagged`);
  if (!res.ok) throw new Error(`Failed to fetch flagged transactions: ${res.status}`);
  return res.json();
}

export async function investigate(
  transactionId: string,
  question?: string
): Promise<InvestigateResponse> {
  const res = await fetch(`${BASE_URL}/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transaction_id: transactionId, question }),
  });
  if (!res.ok) throw new Error(`Investigation failed: ${res.status}`);
  return res.json();
}
