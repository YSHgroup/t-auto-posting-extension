import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { OpportunityItem } from "../types";

export function OpportunitiesPage() {
  const [items, setItems] = useState<OpportunityItem[]>([]);

  useEffect(() => {
    void api.listOpportunities().then(setItems);
  }, []);

  const investment = items.filter((i) => i.category === "investment");
  const partnership = items.filter((i) => i.category === "partnership");

  const section = (title: string, list: OpportunityItem[]) => (
    <div className="card">
      <h3>{title}</h3>
      {list.map((o) => (
        <div key={o.id} style={{ borderTop: "1px solid var(--border)", paddingTop: 8, marginTop: 8 }}>
          <strong>@{o.username}</strong> · {o.group_name}
          <p>Evidence: {o.evidence}</p>
          <p>
            Evidence level: {o.evidence_level} · Confidence: {o.confidence}%
          </p>
        </div>
      ))}
    </div>
  );

  return (
    <div>
      <h2 className="page-title">Potential Opportunities</h2>
      <p>The system does not message these users automatically.</p>
      {section("Investment", investment)}
      {section("Partnership", partnership)}
    </div>
  );
}
