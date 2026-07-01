import { useState, useEffect, useRef } from 'react';
import {
  fetchPlanningSessions, fetchPlanningSession,
  createPlanningSession, sendPlanningMessage, finalizePlanningSession,
  reprocessSession, updateSessionNode,
} from '../data/api';

export function usePlanningSession() {
  const [sessions, setSessions]   = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages]   = useState([]);
  const [plan, setPlan]           = useState({});
  const [nodes, setNodes]         = useState([]);
  const [folderStructure, setFolderStructure] = useState([]);
  const [violations, setViolations] = useState([]);
  const [clarifications, setClarifications] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [blockers, setBlockers] = useState([]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [initializing, setInit]   = useState(true);
  const [finalized, setFinalized] = useState(false);
  const [error, setError]         = useState(null);
  const bottomRef = useRef(null);

  function applySession(session) {
    setSessionId(session.session_id);
    setMessages(session.chat_history || []);
    setPlan(session.implementation_plan || {});
    setNodes(session.inferred_nodes || []);
    setFolderStructure(session.session_folder_structure || []);
    setViolations(session.violations || []);
    setClarifications(session.clarifications || []);
    setSuggestions(session.suggestions || []);
    setBlockers(session.blockers || []);
    setFinalized(session.status === 'finalized');
    setError(null);
  }

  function updateSessionInList(id, chatHistory) {
    const userMsgs = chatHistory.filter(m => m.role === 'user');
    const first = userMsgs[0]?.content || '';
    const title = first.length > 44 ? first.slice(0, 44) + '…' : first || 'New Session';
    setSessions(prev => prev.map(s =>
      s.session_id === id ? { ...s, title, message_count: userMsgs.length } : s
    ));
  }

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
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, clarifications, suggestions, blockers]);

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
      setFolderStructure([]);
      setViolations([]);
      setClarifications([]);
      setSuggestions([]);
      setBlockers([]);
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
      setMessages(session.chat_history);
      setPlan(session.implementation_plan || {});
      setNodes(session.inferred_nodes || []);
      setFolderStructure(session.session_folder_structure || []);
      setViolations(session.violations || []);
      setClarifications(session.clarifications || []);
      setSuggestions(session.suggestions || []);
      setBlockers(session.blockers || []);
      updateSessionInList(sessionId, session.chat_history);
    } catch (err) {
      setMessages([...optimistic, { role: 'error', content: err.message }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleReprocess() {
    if (!sessionId || finalized) return;
    setLoading(true);
    setError(null);
    try {
      const session = await reprocessSession(sessionId);
      setPlan(session.implementation_plan || {});
      setNodes(session.inferred_nodes || []);
      setViolations(session.violations || []);
    } catch (err) {
      setError(`Reprocess failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateNode(nodeData) {
    if (!sessionId || finalized) return null;
    setError(null);
    try {
      const session = await updateSessionNode(sessionId, nodeData);
      setNodes(session.inferred_nodes || []);
      setPlan(session.implementation_plan || {});
      return session;
    } catch (err) {
      setError(`Update failed: ${err.message}`);
      return null;
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

  return {
    sessions, sessionId, messages, plan, nodes, folderStructure, violations,
    clarifications, suggestions, blockers,
    input, loading, initializing, finalized, error,
    bottomRef,
    setInput, createNew, switchToSession,
    handleSend, handleFinalize, handleKeyDown,
    handleReprocess, handleUpdateNode,
  };
}
