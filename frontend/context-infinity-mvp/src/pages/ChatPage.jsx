import { useState } from 'react';
import { usePlanningSession } from '../hooks/usePlanningSession';
import SessionsSidebar from '../components/chat/SessionsSidebar';
import ChatPanel from '../components/chat/ChatPanel';
import PlanPanel from '../components/chat/PlanPanel';
import ViolationModal from '../components/chat/ViolationModal';

export default function ChatPage() {
  const {
    sessions, sessionId, messages, plan, nodes, folderStructure, violations,
    clarifications, suggestions, blockers,
    input, loading, initializing, finalized, error,
    bottomRef,
    setInput, createNew, switchToSession,
    handleSend, handleFinalize, handleKeyDown,
    handleReprocess, handleUpdateNode,
  } = usePlanningSession();

  const [dismissedAtMsgCount, setDismissedAtMsgCount] = useState(null);
  const msgCount = messages.filter(m => m.role === 'user').length;
  const showViolations = violations.length > 0 && dismissedAtMsgCount !== msgCount;

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
        clarifications={clarifications}
        suggestions={suggestions}
        blockers={blockers}
        onInputChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onSend={handleSend}
        onFinalize={handleFinalize}
        nodeCount={nodes.length}
      />
      <PlanPanel
        plan={plan}
        nodes={nodes}
        folderStructure={folderStructure}
        finalized={finalized}
        onUpdateNode={handleUpdateNode}
        onReprocess={handleReprocess}
      />

      {showViolations && (
        <ViolationModal
          violations={violations}
          onClose={() => setDismissedAtMsgCount(msgCount)}
          onReprocess={handleReprocess}
        />
      )}
    </div>
  );
}
