import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { conductoresApi } from '../services/api.js';

export default function Conductores() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await conductoresApi.get('/conductores');
      setItems(r.data?.items || r.data || []);
    } catch (e) {
      setMsg({ type: 'danger', text: 'Error cargando conductores' });
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    if (!confirm('¿Eliminar conductor?')) return;
    await conductoresApi.delete(`/conductores/${id}`);
    load();
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">👤 Conductores</div>
          <Link to="/conductores/nuevo"><button className="btn-primary">+ Nuevo Conductor</button></Link>
        </div>
        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
        {loading ? <div className="empty">Cargando...</div> :
          items.length === 0 ? <div className="empty">Sin conductores registrados</div> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>DNI</th><th>Nombre</th><th>Licencia</th><th>Categoría</th>
                  <th>Vencimiento</th><th>Disponibilidad</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map(c => (
                  <tr key={c.id}>
                    <td>{c.dni}</td>
                    <td>{c.nombre} {c.apellidos}</td>
                    <td>{c.licencia_numero}</td>
                    <td>{c.licencia_categoria}</td>
                    <td>{c.licencia_vencimiento}</td>
                    <td>
                      <span className={`badge badge-${c.disponibilidad === 'DISPONIBLE' ? 'success' : 'warning'}`}>
                        {c.disponibilidad || 'N/D'}
                      </span>
                    </td>
                    <td className="actions">
                      <button className="btn-danger" onClick={() => remove(c.id)}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
