import { useState, useEffect, useRef } from 'react';
import {
  fetchPlanningSessions, fetchPlanningSession,
  createPlanningSession, sendPlanningMessage, finalizePlanningSession,
} from '../data/api';

export default function ChatPage() {
  const [sessions, setSessions]   = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages]   = useState([]);
  const [plan, setPlan]           = useState({});
  const [nodes, setNodes]         = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [initializing, setInit]   = useState(true);
  const [finalized, setFinalized] = useState(false);
  const [error, setError]         = useState(null);
  const bottomRef = useRef(null);

  // Apply a full session payload to component state
  function applySession(session) {
    setSessionId(session.session_id);
    setMessages(session.chat_history || []);
    setPlan(session.implementation_plan || {});
    setNodes(session.inferred_nodes || []);
    setFinalized(session.status === 'finalized');
    setError(null);
  }

  // Update the sidebar entry for a session after it changes
  function updateSessionInList(id, chatHistory) {
    const userMsgs = chatHistory.filter(m => m.role === 'user');
    const first = userMsgs[0]?.content || '';
    const title = first.length > 44 ? first.slice(0, 44) + '…' : first || 'New Session';
    setSessions(prev => prev.map(s =>
      s.session_id === id ? { ...s, title, message_count: userMsgs.length } : s
    ));
  }

  // ── Initialise: fetch session list, load most recent or create new ────

  useEffect(() => {
    async function init() {
      try {
        const { sessions: list } = await fetchPlanningSessions();
        setSessions(list);
        if (list.length > 0) {
          const session = await fetchPlanningSession(list[0].session_id);
          applySession(session);
        } else {
          await createNew();
        }
      } catch {
        setError('Could not reach backend — is it running?');
      } finally {
        setInit(false);
      }
    }
    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll chat to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // ── Session actions ───────────────────────────────────────────────────

  async function createNew() {
    setInit(true);
    setError(null);
    try {
      const { session_id } = await createPlanningSession();
      const newMeta = { session_id, title: 'New Session', message_count: 0, status: 'planning' };
      setSessions(prev => [newMeta, ...prev]);
      setSessionId(session_id);
      setMessages([]);
      setPlan({});
      setNodes([]);
      setFinalized(false);
    } catch {
      setError('Could not start session — is the backend running?');
    } finally {
      setInit(false);
    }
  }

  async function switchToSession(id) {
    if (id === sessionId) return;
    try {
      const session = await fetchPlanningSession(id);
      applySession(session);
    } catch {
      setError('Could not load session.');
    }
  }

  // ── Chat actions ──────────────────────────────────────────────────────

  async function handleSend() {
    const text = input.trim();
    if (!text || loading || !sessionId || finalized) return;
    setInput('');
    setLoading(true);
    setError(null);

    const optimistic = [...messages, { role: 'user', content: text }];
    setMessages(optimistic);

    try {
      const session = await sendPlanningMessage(sessionId, text);
      const newMsgs  = session.chat_history;
      const newPlan  = session.implementation_plan || {};
      const newNodes = session.inferred_nodes || [];
      setMessages(newMsgs);
      setPlan(newPlan);
      setNodes(newNodes);
      updateSessionInList(sessionId, newMsgs);
    } catch (err) {
      setMessages([...optimistic, { role: 'error', content: err.message }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleFinalize() {
    if (!sessionId || finalized || nodes.length === 0) return;
    setError(null);
    try {
      await finalizePlanningSession(sessionId);
      setFinalized(true);
      setSessions(prev => prev.map(s =>
        s.session_id === sessionId ? { ...s, status: 'finalized' } : s
      ));
    } catch (err) {
      setError(`Finalize failed: ${err.message}`);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  // ── Loading screen ────────────────────────────────────────────────────

  if (initializing) {
    return (
      <div className="planner-shell planner-shell--centered">
        <div className="planner-init-msg">
          <span className="planner-spinner" /> Initializing session…
        </div>
      </div>
    );
  }

  // ── Main render ───────────────────────────────────────────────────────

  return (
    <div className="planner-shell">

      {/* ── Sessions sidebar ─────────────────────────────────────────── */}
      <div className="planner-sessions-sidebar">
        <div className="planner-panel-header">
          <span className="planner-panel-title">Sessions</span>
          <button
            className="planner-btn-new-session"
            onClick={createNew}
            title="New session"
          >
            +
          </button>
        </div>
        <div className="planner-sessions-list">
          {sessions.length === 0 && (
            <p className="planner-sessions-empty">No sessions yet</p>
          )}
          {sessions.map(s => (
            <button
              key={s.session_id}
              className={`planner-session-item${s.session_id === sessionId ? ' planner-session-item--active' : ''}`}
              onClick={() => switchToSession(s.session_id)}
            >
              <span className="planner-session-title">{s.title || 'New Session'}</span>
              <div className="planner-session-meta">
                {s.message_count > 0 && (
                  <span className="planner-session-count">
                    {s.message_count} msg{s.message_count !== 1 ? 's' : ''}
                  </span>
                )}
                {s.status === 'finalized' && (
                  <span className="planner-session-done">done</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Chat panel ───────────────────────────────────────────────── */}
      <div className="planner-chat-panel">
        <div className="planner-panel-header">
          <span className="planner-panel-title">Chat</span>
          {finalized && <span className="planner-badge planner-badge--done">Finalized</span>}
        </div>

        <div className="planner-messages">
          {messages.length === 0 && (
            <div className="planner-empty">
              <span className="planner-empty-icon">&#9670;</span>
              <p>Describe the feature you want to plan.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`planner-bubble planner-bubble--${msg.role}`}>
              <span className="planner-bubble-label">
                {msg.role === 'user' ? 'You' : msg.role === 'error' ? '!' : 'Planner'}
              </span>
              <div className="planner-bubble-text">{msg.content}</div>
            </div>
          ))}

          {loading && (
            <div className="planner-bubble planner-bubble--assistant planner-bubble--thinking">
              <span className="planner-bubble-label">Planner</span>
              <div className="planner-bubble-text chat-thinking-dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="planner-input-area">
          {error && <div className="planner-error-banner">{error}</div>}
          <textarea
            className="planner-textarea"
            rows={3}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={finalized ? 'Session finalized.' : 'Describe your feature… (Enter to send, Shift+Enter for newline)'}
            disabled={loading || finalized}
          />
          <div className="planner-input-actions">
            <button
              className="planner-btn planner-btn--send"
              onClick={handleSend}
              disabled={loading || finalized || !input.trim()}
            >
              {loading ? 'Thinking…' : 'Send'}
            </button>
            <button
              className="planner-btn planner-btn--finalize"
              onClick={handleFinalize}
              disabled={finalized || nodes.length === 0}
              title={nodes.length === 0 ? 'Chat first to infer decisions' : 'Save decisions to database'}
            >
              {finalized ? '✓ Finalized' : 'Finalize'}
            </button>
          </div>
        </div>
      </div>

      {/* ── Right: Plan + Nodes ──────────────────────────────────────── */}
      <div className="planner-right-panel">

        <div className="planner-plan-panel">
          <div className="planner-panel-header">
            <span className="planner-panel-title">Implementation Plan</span>
            <span className="planner-panel-count">{Object.keys(plan).length} sections</span>
          </div>
          <div className="planner-panel-body">
            {Object.keys(plan).length === 0 ? (
              <div className="planner-empty planner-empty--sm">
                Plan sections will appear as you chat.
              </div>
            ) : (
              Object.entries(plan).map(([key, value]) => (
                <div key={key} className="plan-section">
                  <div className="plan-section-id">{key.replace(/_/g, ' ')}</div>
                  <div className="plan-section-content">{value}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="planner-nodes-panel">
          <div className="planner-panel-header">
            <span className="planner-panel-title">Inferred Decisions</span>
            <span className="planner-panel-count">{nodes.length} nodes</span>
          </div>
          <div className="planner-panel-body">
            {nodes.length === 0 ? (
              <div className="planner-empty planner-empty--sm">
                Architectural decisions will be extracted from your conversation.
              </div>
            ) : (
              nodes.map((node, i) => (
                <div key={i} className="planner-node-card">
                  <div className="planner-node-top">
                    <span className="planner-node-title">{node.title}</span>
                    <span className={`planner-conf ${
                      node.confidence >= 0.85 ? 'planner-conf--high'
                      : node.confidence >= 0.65 ? 'planner-conf--med'
                      : 'planner-conf--low'
                    }`}>
                      {Math.round(node.confidence * 100)}%
                    </span>
                  </div>
                  <div className="planner-node-decision">{node.decision}</div>
                  {node.rationale && (
                    <div className="planner-node-rationale">{node.rationale}</div>
                  )}
                  {node.tradeoffs?.length > 0 && (
                    <ul className="planner-node-tradeoffs">
                      {node.tradeoffs.map((t, ti) => <li key={ti}>{t}</li>)}
                    </ul>
                  )}
                  <div className="planner-node-footer">
                    {node.tags?.length > 0 && (
                      <div className="planner-node-tags">
                        {node.tags.map((t, ti) => (
                          <span key={ti} className="planner-tag">{t}</span>
                        ))}
                      </div>
                    )}
                    {node.artifact_ref && (
                      <span className="planner-artifact-ref">{node.artifact_ref}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
