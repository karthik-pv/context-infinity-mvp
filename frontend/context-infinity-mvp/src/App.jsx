import { Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import ContextPage from './pages/ContextPage';
import ChatPage from './pages/ChatPage';
import ProjectPage from './pages/ProjectPage';

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <Routes>
        <Route path="/" element={<ContextPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/project" element={<ProjectPage />} />
      </Routes>
    </div>
  );
}
