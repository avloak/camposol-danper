import { Link } from 'react-router-dom';

const cards = [
  { to: '/flotas',      title: 'Gestión de Flotas',     desc: 'CRUD de buses, alertas SOAT/RT', icon: '🚌', color: '#0d6efd' },
  { to: '/conductores', title: 'Conductores',           desc: 'Perfiles, licencias, legajo',    icon: '👤', color: '#198754' },
  { to: '/horarios',    title: 'Horarios y Rutas',      desc: 'Asignaciones y turnos',          icon: '📅', color: '#fd7e14' },
  { to: '/descansos',   title: 'Descansos Médicos',     desc: 'Procesa PDFs con IA',            icon: '🏥', color: '#dc3545' },
  { to: '/deudas',      title: 'Deudas / Infracciones', desc: 'Workflow de reportes IA',        icon: '💰', color: '#6f42c1' }
];

export default function Dashboard() {
  return (
    <div>
      <div className="card">
        <div className="card-title">Bienvenido a ProntoBus</div>
        <p style={{ marginTop: 8, color: '#666' }}>
          Plataforma integral para la gestión de flotas, conductores, horarios y procesamiento
          automatizado de descansos médicos y deudas por infracciones con Inteligencia Artificial.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 16
      }}>
        {cards.map(c => (
          <Link key={c.to} to={c.to} style={{ textDecoration: 'none' }}>
            <div className="card" style={{ borderLeft: `4px solid ${c.color}`, cursor: 'pointer', height: '100%' }}>
              <div style={{ fontSize: 32 }}>{c.icon}</div>
              <div style={{ fontWeight: 600, marginTop: 10, color: '#222' }}>{c.title}</div>
              <div style={{ color: '#666', fontSize: 13, marginTop: 4 }}>{c.desc}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
