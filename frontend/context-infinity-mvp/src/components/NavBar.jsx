import { NavLink } from 'react-router-dom';

export default function NavBar() {
  return (
    <header className="app-header">
      <h1>Context Infinity</h1>
      <nav className="app-nav">
        <NavLink to="/" end className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '')}>
          Context
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '')}>
          Chat
        </NavLink>
        <NavLink to="/project" className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '')}>
          Project
        </NavLink>
      </nav>
    </header>
  );
}
