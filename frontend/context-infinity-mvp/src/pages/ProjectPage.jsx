import { useState } from 'react';
import { useProject } from '../hooks/useProject';
import FolderTree from '../components/project/FolderTree';
import DriftModal from '../components/project/DriftModal';

export default function ProjectPage() {
  const {
    projectPath, projectBrief, folderStructure, actualFolderStructure,
    loading, saving, syncing, error,
    setProjectPath, setProjectBrief,
    savePath, saveBrief, syncFolders,
  } = useProject();

  const [pathInput, setPathInput] = useState('');
  const [briefInput, setBriefInput] = useState('');
  const [editingPath, setEditingPath] = useState(false);
  const [editingBrief, setEditingBrief] = useState(false);
  const [drift, setDrift] = useState(null);

  if (loading) {
    return (
      <div className="project-shell project-shell--centered">
        <span className="planner-spinner" /> Loading project…
      </div>
    );
  }

  async function handleSync() {
    const actual = await syncFolders();
    if (actual) {
      const plannedSet = new Set(folderStructure);
      const actualSet = new Set(actual);
      const missing = folderStructure.filter(p => !actualSet.has(p));
      const extra = actual.filter(p => !plannedSet.has(p));
      if (missing.length > 0 || extra.length > 0) {
        setDrift({ missing, extra });
      }
    }
  }

  return (
    <div className="project-shell">
      <div className="project-left">
        <div className="project-panel-header">
          <span className="project-panel-title">Folder Structure</span>
          <button
            className="project-sync-btn"
            onClick={handleSync}
            disabled={syncing || !projectPath}
            title="Scan actual filesystem and compare"
          >
            {syncing ? 'Syncing…' : 'Sync'}
          </button>
        </div>
        <div className="project-tree-split">
          <div className="project-tree-half">
            <div className="project-tree-half-label">Planned</div>
            <div className="project-tree-container">
              <FolderTree paths={folderStructure} />
            </div>
          </div>
          <div className="project-tree-half">
            <div className="project-tree-half-label">Actual</div>
            <div className="project-tree-container">
              <FolderTree paths={actualFolderStructure} />
            </div>
          </div>
        </div>
      </div>

      <div className="project-right">
        <div className="project-right-top">
          <label className="project-field-label">Project Path</label>
          <div className="project-path-row">
            <input
              className="project-path-input"
              value={editingPath ? pathInput : projectPath}
              placeholder="/path/to/your/project"
              onChange={e => { setPathInput(e.target.value); setEditingPath(true); }}
              onBlur={() => {
                if (editingPath && pathInput !== projectPath) savePath(pathInput);
                setEditingPath(false);
              }}
              onKeyDown={e => {
                if (e.key === 'Enter') e.target.blur();
              }}
            />
          </div>

          <label className="project-field-label">Project Brief</label>
          <textarea
            className="project-brief-input"
            value={editingBrief ? briefInput : projectBrief}
            placeholder="A brief summary of the project…"
            rows="3"
            onChange={e => { setBriefInput(e.target.value); setEditingBrief(true); }}
            onBlur={() => {
              if (editingBrief && briefInput !== projectBrief) saveBrief(briefInput);
              setEditingBrief(false);
            }}
          />
          {saving && <span className="project-saving">Saving…</span>}
          {error && <span className="project-error">{error}</span>}
        </div>

        <div className="project-right-summary">
          <div className="project-panel-header">
            <span className="project-panel-title">Project Summary</span>
          </div>
          <div className="project-summary-body">
            {projectBrief ? (
              <pre className="project-summary-text">{projectBrief}</pre>
            ) : (
              <p className="project-summary-empty">
                No project brief yet. Enter one above to see it here.
              </p>
            )}
          </div>
        </div>
      </div>

      {drift && <DriftModal drift={drift} onClose={() => setDrift(null)} />}
    </div>
  );
}
