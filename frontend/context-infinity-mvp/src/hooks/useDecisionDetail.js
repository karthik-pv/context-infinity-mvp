import { useEffect, useState } from 'react';
import { fetchDecisionById, updateDecision } from '../data/api';

export function useDecisionDetail(nodeId, onClose) {
  const [node, setNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [mode, setMode] = useState('view');
  const [editData, setEditData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setNode(null);
    setFetchError(null);
    setMode('view');
    fetchDecisionById(nodeId)
      .then(data => { setNode(data); setLoading(false); })
      .catch(err => { setFetchError(err.message); setLoading(false); });
  }, [nodeId]);

  useEffect(() => {
    function onKey(e) {
      if (e.key !== 'Escape') return;
      if (mode === 'edit') setMode('view');
      else onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, mode]);

  function enterEdit() {
    setEditData({
      title:      node.title,
      decision:   node.decision,
      rationale:  node.rationale || '',
      tradeoffs:  (node.tradeoffs || []).join('\n'),
      confidence: node.confidence,
      tags:       (node.tags || []).join('\n'),
    });
    setSaveError(null);
    setMode('edit');
  }

  function cancelEdit() {
    setMode('view');
    setSaveError(null);
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await updateDecision(nodeId, {
        title:      editData.title.trim(),
        decision:   editData.decision.trim(),
        rationale:  editData.rationale.trim() || null,
        tradeoffs:  editData.tradeoffs.split('\n').map(s => s.trim()).filter(Boolean),
        confidence: parseFloat(editData.confidence),
        tags:       editData.tags.split('\n').map(s => s.trim()).filter(Boolean),
      });
      setNode(updated);
      setMode('view');
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function field(key) {
    return e => setEditData(prev => ({ ...prev, [key]: e.target.value }));
  }

  return {
    node, loading, fetchError,
    mode, editData, saving, saveError,
    enterEdit, cancelEdit, handleSave, field,
  };
}
