import { NavLink } from 'react-router-dom';

export default function NavBar() {
  return (
    <header className="app-header">
      <span className="logo-mark">&#9670;</span>
      <h1>Context Infinity</h1>
      <nav className="app-nav">
        <NavLink to="/" end className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '')}>
          Context
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link--active' : '')}>
          Chat
        </NavLink>
      </nav>
    </header>
  );
}
