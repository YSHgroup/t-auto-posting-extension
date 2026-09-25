import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import type { GroupAnalysis, GroupDetail } from "../types";

export function GroupDetailPage() {
  const { id = "" } = useParams();
  const [search] = useSearchParams();
  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [analysis, setAnalysis] = useState<GroupAnalysis | null>(null);
  const [history, setHistory] = useState<GroupAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const g = await api.getGroup(id);
        setGroup(g);
        const list = await api.listAnalysis(id);
        setHistory(list);
        if (list[0]) setAnalysis(list[0]);
        if (search.get("analyze") === "1") await runAnalyze();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load group");
      }
    })();
  }, [id]);

  const runAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const a = await api.analyzeGroup(id);
      setAnalysis(a);
      setHistory(await api.listAnalysis(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const explore = async () => {
    setLoading(true);
    try {
      await api.scanOpportunities(id);
      alert("Opportunity scan complete. See Opportunities page.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  if (!group) return <p>Loading...</p>;

  return (
    <div>
      <Link to="/groups">← Back</Link>
      <h2 className="page-title">{group.name}</h2>
      <p>@{group.username} · {group.member_count.toLocaleString()} members</p>
      <p>{group.description}</p>
      <div className="row">
        <button type="button" className="btn btn-primary" onClick={() => void runAnalyze()} disabled={loading}>
          {analysis ? "Re-analyze" : "Analyze Group"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void explore()} disabled={loading}>
          Explore Opportunities
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void api.addFeed(group.external_id)}>
          Add to Feed
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {analysis && (
        <div className="card">
          <h3>Group Overview</h3>
          <p>{analysis.summary}</p>
          <h4>What people do</h4>
          <ul>
            {analysis.activities.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
          <p>Likely member types: {analysis.member_types.join(", ")}</p>
          <h4>Partnership suitability</h4>
          <p>
            {analysis.partnership_status} ({Math.round(analysis.partnership_confidence * 100)}%) —{" "}
            {analysis.partnership_reason}
          </p>
          <h4>Job posting suitability</h4>
          <p>
            {analysis.job_status} ({Math.round(analysis.job_confidence * 100)}%) — {analysis.job_reason}
          </p>
          <h4>Risks</h4>
          <ul>
            {analysis.risks.map((r) => (
              <li key={r.text}>
                [{r.source}] {r.text}
              </li>
            ))}
          </ul>
          <h4>Recommended posting style</h4>
          <p>{analysis.posting_style.join(" · ")}</p>
        </div>
      )}
      {history.length > 1 && (
        <div className="card">
          <h3>Previous analysis</h3>
          {history.slice(1, 5).map((h) => (
            <button key={h.id} type="button" className="btn btn-ghost" onClick={() => setAnalysis(h)}>
              {new Date(h.created_at).toLocaleString()}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
