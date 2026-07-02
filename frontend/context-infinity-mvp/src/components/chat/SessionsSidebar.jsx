export default function SessionsSidebar({ sessions, sessionId, onCreate, onSwitch, onDelete }) {
  return (
    <div className="planner-sessions-sidebar">
      <div className="planner-panel-header">
        <span className="planner-panel-title">Sessions</span>
        <button className="planner-btn-new-session" onClick={onCreate} title="New session">
          +
        </button>
      </div>
      <div className="planner-sessions-list">
        {sessions.length === 0 && (
          <p className="planner-sessions-empty">No sessions yet</p>
        )}
        {sessions.map(s => (
          <div
            key={s.session_id}
            className={`planner-session-item${s.session_id === sessionId ? ' planner-session-item--active' : ''}`}
            onClick={() => onSwitch(s.session_id)}
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
              <button
                className="planner-session-delete"
                onClick={(e) => { e.stopPropagation(); onDelete(s.session_id); }}
                title="Delete session"
              >
                &#x2715;
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
