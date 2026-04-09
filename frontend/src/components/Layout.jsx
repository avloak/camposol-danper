import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import './layout.css';

const links = [
  { to: '/',             label: 'Dashboard',     icon: '🏠' },
  { to: '/flotas',       label: 'Flotas',        icon: '🚌' },
  { to: '/conductores',  label: 'Conductores',   icon: '👤' },
  { to: '/horarios',     label: 'Horarios',      icon: '📅' },
  { to: '/descansos',             label: 'Descansos (IA)',  icon: '🏥' },
  { to: '/descansos/solicitudes', label: 'Solicitudes Med.',icon: '📋' },
  { to: '/deudas',                label: 'Deudas',          icon: '💰' }
];

export default function Layout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="layout">
      <header className="topbar">
        <button className="menu-btn" onClick={() => setOpen(!open)} aria-label="Menu">
          ☰
        </button>
        <div className="brand">🚌 ProntoBus</div>
        <div className="topbar-right">v1.0</div>
      </header>

      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <nav>
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            >
              <span className="icon">{l.icon}</span>
              <span>{l.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {open && <div className="overlay" onClick={() => setOpen(false)} />}

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
