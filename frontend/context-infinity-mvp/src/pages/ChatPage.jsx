import { useState } from 'react';
import { usePlanningSession } from '../hooks/usePlanningSession';
import SessionsSidebar from '../components/chat/SessionsSidebar';
import ChatPanel from '../components/chat/ChatPanel';
import PlanPanel from '../components/chat/PlanPanel';
import ViolationModal from '../components/chat/ViolationModal';

export default function ChatPage() {
  const {
    sessions, sessionId, messages, plan, nodes, folderStructure, violations,
    input, loading, initializing, finalized, error,
    bottomRef,
    setInput, createNew, switchToSession, handleDelete,
    handleSend, handleFinalize, handleKeyDown,
    handleReprocess, handleUpdateNode,
  } = usePlanningSession();

  const [showViolationModal, setShowViolationModal] = useState(false);

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
        onDelete={handleDelete}
      />
      <ChatPanel
        messages={messages}
        loading={loading}
        finalized={finalized}
        input={input}
        error={error}
        bottomRef={bottomRef}
        violations={violations}
        onShowViolations={() => setShowViolationModal(true)}
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

      {showViolationModal && violations.length > 0 && (
        <ViolationModal
          violations={violations}
          onClose={() => setShowViolationModal(false)}
          onReprocess={handleReprocess}
        />
      )}
    </div>
  );
}
