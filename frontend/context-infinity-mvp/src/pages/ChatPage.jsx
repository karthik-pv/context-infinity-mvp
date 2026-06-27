import { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../data/api';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setLoading(true);

    try {
      const { reply } = await sendChatMessage(text);
      setMessages(prev => [...prev, { role: 'assistant', text: reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', text: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-shell">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <span className="chat-empty-icon">&#9670;</span>
            <p>Ask anything about your codebase decisions.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${msg.role}`}>
            <span className="chat-bubble-label">
              {msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'CI' : '!'}
            </span>
            <p className="chat-bubble-text">{msg.text}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble chat-bubble--assistant chat-bubble--thinking">
            <span className="chat-bubble-label">CI</span>
            <p className="chat-bubble-text chat-thinking-dots">
              <span>.</span><span>.</span><span>.</span>
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          placeholder="Ask about your codebase…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={loading}
        />
        <button
          className="chat-send"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}
