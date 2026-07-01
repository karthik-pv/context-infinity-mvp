import { useState, useEffect, useCallback } from 'react';
import {
  fetchProjectInfo, updateProjectInfo, syncFolderStructure,
  addPathsToPlanned, updateBriefEntry, addBriefEntry, deleteBriefEntry,
} from '../data/api';

export function useProject() {
  const [projectPath, setProjectPath] = useState('');
  const [projectBrief, setProjectBrief] = useState([]);
  const [folderStructure, setFolderStructure] = useState([]);
  const [actualFolderStructure, setActualFolderStructure] = useState([]);
  const [inputTokens, setInputTokens] = useState(0);
  const [outputTokens, setOutputTokens] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjectInfo()
      .then(info => {
        setProjectPath(info.project_path || '');
        setProjectBrief(info.project_brief || []);
        setFolderStructure(info.folder_structure || []);
        setActualFolderStructure(info.actual_folder_structure || []);
        setInputTokens(info.input_tokens_consumed || 0);
        setOutputTokens(info.output_tokens_consumed || 0);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const savePath = useCallback(async (path) => {
    setSaving(true);
    setError(null);
    try {
      const info = await updateProjectInfo({ project_path: path });
      setProjectPath(info.project_path);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }, []);

  const syncFolders = useCallback(async () => {
    setSyncing(true);
    setError(null);
    try {
      const result = await syncFolderStructure();
      setActualFolderStructure(result.actual_folder_structure || []);
      return result.actual_folder_structure || [];
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setSyncing(false);
    }
  }, []);

  const addPaths = useCallback(async (paths) => {
    setSaving(true);
    setError(null);
    try {
      const result = await addPathsToPlanned(paths);
      setFolderStructure(result.folder_structure || []);
      return result.folder_structure || [];
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

  const editBrief = useCallback(async (index, text) => {
    setSaving(true);
    setError(null);
    try {
      const result = await updateBriefEntry(index, text);
      setProjectBrief(result.project_brief || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }, []);

  const addBrief = useCallback(async (text) => {
    setSaving(true);
    setError(null);
    try {
      const result = await addBriefEntry(text);
      setProjectBrief(result.project_brief || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }, []);

  const removeBrief = useCallback(async (index) => {
    setSaving(true);
    setError(null);
    try {
      const result = await deleteBriefEntry(index);
      setProjectBrief(result.project_brief || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }, []);

  return {
    projectPath, projectBrief, folderStructure, actualFolderStructure,
    inputTokens, outputTokens,
    loading, saving, syncing, error,
    setProjectPath,
    savePath, syncFolders,
    addPaths, editBrief, addBrief, removeBrief,
  };
}
