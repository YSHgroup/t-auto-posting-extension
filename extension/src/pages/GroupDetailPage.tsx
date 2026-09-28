import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import type { GroupAnalysis, GroupDetail, GroupMessage } from "../types";

export function GroupDetailPage() {
  const { id = "" } = useParams();
  const [search] = useSearchParams();
  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [analysis, setAnalysis] = useState<GroupAnalysis | null>(null);
  const [history, setHistory] = useState<GroupAnalysis[]>([]);
  const [messages, setMessages] = useState<GroupMessage[]>([]);
  const [messageImport, setMessageImport] = useState("");
  const [replyUsername, setReplyUsername] = useState("");
  const [replyText, setReplyText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const g = await api.getGroup(id);
        setGroup(g);
        setMessages(await api.getGroupMessages(id, 50));
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

  const importMessages = async () => {
    const rows = messageImport.split("\n").map((line) => line.trim()).filter(Boolean).slice(0, 500);
    if (!rows.length) return;
    try {
      const result = await api.importObservedMessages(id, rows);
      setMessageImport("");
      setMessages(await api.getGroupMessages(id, 50));
      alert(`Imported ${result.imported} message lines for your account. The extension did not read them from Telegram.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Message import failed");
    }
  };

  const logReply = async () => {
    try {
      await api.logManualReply(id, replyUsername.trim(), replyText.trim());
      setReplyText("");
      alert("Reply saved as a notification for your account. It was not collected automatically.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reply logging failed");
    }
  };

  if (!group) return <p>Loading...</p>;

  return (
    <div>
      <Link to="/groups">← Back</Link>
      <h2 className="page-title">{group.name}</h2>
      <p>@{group.username} · {group.member_count.toLocaleString()} members</p>
      <p>{group.description}</p>
      {group.telegram_url && (
        <p><a href={group.telegram_url} target="_blank" rel="noreferrer">Open Telegram group</a></p>
      )}
      <div className="row">
        <button type="button" className="btn btn-primary" onClick={() => void runAnalyze()} disabled={loading}>
          {analysis ? "Re-analyze" : "Analyze Group"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void explore()} disabled={loading}>
          Explore Opportunities
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void api.addFeed(group.external_id, group.telegram_url)}>
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
      <div className="card">
        <h3>Message evidence</h3>
        <p className="muted">To analyze a real group, manually copy message text from Telegram and paste it here (one message per line; prefix as @username: text to attribute a speaker). Max 500. This extension does not collect chat messages. You can also paste only information you are permitted to share.</p>
        <textarea className="input" rows={5} value={messageImport} onChange={(e) => setMessageImport(e.target.value)} placeholder="Paste copied message text here" />
        <button type="button" className="btn btn-primary" onClick={() => void importMessages()}>
          Import pasted messages
        </button>
        <h3>Recent imported/provider messages</h3>
        {messages.length === 0 && <p>No messages available.</p>}
        {messages.slice().reverse().map((message) => (
          <div key={message.id} className="message-row">
            <strong>{message.is_app_post ? "You" : `@${message.username || "unknown"}`}</strong>
            <span>{new Date(message.created_at).toLocaleString()}</span>
            <p>{message.content}</p>
          </div>
        ))}
      </div>
      <div className="card">
        <h3>Log a copied reply</h3>
        <p className="muted">Paste a reply you chose to record. Telegram replies are not monitored automatically.</p>
        <input className="input" value={replyUsername} onChange={(e) => setReplyUsername(e.target.value)} placeholder="Telegram username" />
        <textarea className="input" rows={3} value={replyText} onChange={(e) => setReplyText(e.target.value)} placeholder="Copied reply text" />
        <button type="button" className="btn btn-primary" disabled={!replyUsername.trim() || !replyText.trim()} onClick={() => void logReply()}>
          Save as notification
        </button>
      </div>
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
