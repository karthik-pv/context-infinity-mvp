import { usePlanningSession } from '../hooks/usePlanningSession';
import SessionsSidebar from '../components/chat/SessionsSidebar';
import ChatPanel from '../components/chat/ChatPanel';
import PlanPanel from '../components/chat/PlanPanel';

export default function ChatPage() {
  const {
    sessions, sessionId, messages, plan, nodes, folderStructure,
    input, loading, initializing, finalized, error,
    bottomRef,
    setInput, createNew, switchToSession,
    handleSend, handleFinalize, handleKeyDown,
  } = usePlanningSession();

  if (initializing) {
    return (
      <div className="planner-shell planner-shell--centered">
        <div className="planner-init-msg">
          <span className="planner-spinner" /> Initializing session…
        </div>
      </div>
    );
  }

  return (
    <div className="planner-shell">
      <SessionsSidebar
        sessions={sessions}
        sessionId={sessionId}
        onCreate={createNew}
        onSwitch={switchToSession}
      />
      <ChatPanel
        messages={messages}
        loading={loading}
        finalized={finalized}
        input={input}
        error={error}
        bottomRef={bottomRef}
        onInputChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onSend={handleSend}
        onFinalize={handleFinalize}
        nodeCount={nodes.length}
      />
      <PlanPanel plan={plan} nodes={nodes} folderStructure={folderStructure} />
    </div>
  );
}
