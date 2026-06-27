import { Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import ContextPage from './pages/ContextPage';
import ChatPage from './pages/ChatPage';

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <Routes>
        <Route path="/" element={<ContextPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </div>
  );
}
