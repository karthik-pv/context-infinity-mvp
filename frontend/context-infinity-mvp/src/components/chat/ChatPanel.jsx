export default function ChatPanel({
  messages, loading, finalized, input, error, bottomRef,
  clarifications, suggestions, blockers,
  onInputChange, onKeyDown, onSend, onFinalize, nodeCount,
}) {
  const hasPlannerOutput =
    clarifications.length > 0 || suggestions.length > 0 || blockers.length > 0;

  return (
    <div className="planner-chat-panel">
      <div className="planner-panel-header">
        <span className="planner-panel-title">Chat</span>
        {finalized && <span className="planner-badge planner-badge--done">Finalized</span>}
      </div>

      <div className="planner-messages">
        {messages.length === 0 && !loading && (
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

        {!loading && messages.length > 0 && (
          <>
            {clarifications.length > 0 && (
              <div className="planner-bubble planner-bubble--assistant">
                <span className="planner-bubble-label">Clarifications</span>
                <div className="planner-bubble-text planner-output-text">
                  {clarifications.map((q, i) => (
                    <div key={i} className="planner-clarification">
                      <div className="planner-output-item">
                        <span className="planner-output-icon">&#9881;</span>
                        <span>{q.question}</span>
                      </div>
                      {q.options && q.options.length > 0 && (
                        <div className="planner-clarification-options">
                          {q.options.map((opt, j) => (
                            <span key={j} className="planner-clarification-option">
                              {opt}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {suggestions.length > 0 && (
              <div className="planner-bubble planner-bubble--assistant">
                <span className="planner-bubble-label">Suggestions</span>
                <div className="planner-bubble-text planner-output-text">
                  {suggestions.map((s, i) => (
                    <div key={i} className="planner-output-item">
                      <span className="planner-output-icon planner-output-icon--suggestion">&#9728;</span>
                      <span><strong>{s.title}</strong> — {s.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {blockers.length > 0 && (
              <div className="planner-bubble planner-bubble--assistant">
                <span className="planner-bubble-label">Blockers</span>
                <div className="planner-bubble-text planner-output-text">
                  {blockers.map((b, i) => (
                    <div key={i} className="planner-output-item planner-output-item--blocker">
                      <span className="planner-output-icon planner-output-icon--blocker">&#9888;</span>
                      <span><strong>{b.title}</strong> — {b.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!hasPlannerOutput && (
              <div className="planner-bubble planner-bubble--assistant">
                <span className="planner-bubble-label">Planner</span>
                <div className="planner-bubble-text planner-output-text">
                  <span className="planner-output-item">
                    <span className="planner-output-icon">&#10003;</span>
                    <span>Plan updated. No clarifications or suggestions at this time.</span>
                  </span>
                </div>
              </div>
            )}
          </>
        )}

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
          onChange={onInputChange}
          onKeyDown={onKeyDown}
          placeholder={finalized ? 'Session finalized.' : 'Describe your feature… (Enter to send, Shift+Enter for newline)'}
          disabled={loading || finalized}
        />
        <div className="planner-input-actions">
          <button
            className="planner-btn planner-btn--send"
            onClick={onSend}
            disabled={loading || finalized || !input.trim()}
          >
            {loading ? 'Thinking…' : 'Send'}
          </button>
          <button
            className="planner-btn planner-btn--finalize"
            onClick={onFinalize}
            disabled={finalized || nodeCount === 0}
            title={nodeCount === 0 ? 'Chat first to infer decisions' : 'Save decisions to database'}
          >
            {finalized ? '✓ Finalized' : 'Finalize'}
          </button>
        </div>
      </div>
    </div>
  );
}
