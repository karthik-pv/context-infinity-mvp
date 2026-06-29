import { useState, useEffect, useCallback } from 'react';
import { fetchProjectInfo, updateProjectInfo, syncFolderStructure } from '../data/api';

export function useProject() {
  const [projectPath, setProjectPath] = useState('');
  const [projectBrief, setProjectBrief] = useState('');
  const [folderStructure, setFolderStructure] = useState([]);
  const [actualFolderStructure, setActualFolderStructure] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProjectInfo()
      .then(info => {
        setProjectPath(info.project_path || '');
        setProjectBrief(info.project_brief || '');
        setFolderStructure(info.folder_structure || []);
        setActualFolderStructure(info.actual_folder_structure || []);
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

  const saveBrief = useCallback(async (brief) => {
    setSaving(true);
    setError(null);
    try {
      const info = await updateProjectInfo({ project_brief: brief });
      setProjectBrief(info.project_brief);
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

  return {
    projectPath, projectBrief, folderStructure, actualFolderStructure,
    loading, saving, syncing, error,
    setProjectPath, setProjectBrief,
    savePath, saveBrief, syncFolders,
  };
}
