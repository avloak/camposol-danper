import { useEffect, useState } from 'react';
import { horariosApi } from '../services/api.js';

const empty = {
  conductor_id: '', bus_id: '', ruta: '', fecha: '',
  hora_inicio: '', hora_fin: '', estado: 'PROGRAMADO'
};

export default function Horarios() {
  const [items, setItems] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await horariosApi.get('/horarios');
      setItems(r.data?.items || r.data || []);
    } catch (e) { setMsg({ type: 'danger', text: 'Error cargando horarios' }); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openNew = () => { setForm(empty); setEditingId(null); setShow(true); };
  const openEdit = (h) => { setForm({ ...empty, ...h }); setEditingId(h.id); setShow(true); };

  const save = async () => {
    try {
      if (editingId) {
        await horariosApi.put(`/horarios/${editingId}`, form);
      } else {
        await horariosApi.post('/horarios', form);
      }
      setShow(false); load();
    } catch (e) { setMsg({ type: 'danger', text: 'Error al guardar' }); }
  };

  const remove = async (id) => {
    if (!confirm('¿Eliminar asignación?')) return;
    await horariosApi.delete(`/horarios/${id}`);
    load();
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">📅 Horarios y Asignaciones</div>
          <button className="btn-primary" onClick={openNew}>+ Nueva Asignación</button>
        </div>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {loading ? <div className="empty">Cargando...</div> :
          items.length === 0 ? <div className="empty">Sin asignaciones</div> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th><th>Conductor</th><th>Bus</th><th>Ruta</th>
                  <th>Inicio</th><th>Fin</th><th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map(h => (
                  <tr key={h.id}>
                    <td>{h.fecha}</td>
                    <td>{h.conductor_id}</td>
                    <td>{h.bus_id}</td>
                    <td>{h.ruta}</td>
                    <td>{h.hora_inicio}</td>
                    <td>{h.hora_fin}</td>
                    <td>
                      <span className={`badge badge-${h.estado === 'PROGRAMADO' ? 'success' : h.estado === 'CANCELADO' ? 'danger' : 'warning'}`}>
                        {h.estado}
                      </span>
                    </td>
                    <td className="actions">
                      <button className="btn-secondary" onClick={() => openEdit(h)}>Editar</button>
                      <button className="btn-danger" onClick={() => remove(h.id)}>Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {show && (
        <div className="modal-bg" onClick={() => setShow(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 16 }}>{editingId ? 'Editar Asignación' : 'Nueva Asignación'}</h3>
            <div className="form-grid">
              <div><label>Conductor (DNI/ID)</label><input value={form.conductor_id} onChange={e => setForm({ ...form, conductor_id: e.target.value })} /></div>
              <div><label>Bus (Placa/ID)</label><input value={form.bus_id} onChange={e => setForm({ ...form, bus_id: e.target.value })} /></div>
              <div className="full"><label>Ruta</label><input value={form.ruta} onChange={e => setForm({ ...form, ruta: e.target.value })} placeholder="Ej. San Juan - Miraflores" /></div>
              <div><label>Fecha</label><input type="date" value={form.fecha} onChange={e => setForm({ ...form, fecha: e.target.value })} /></div>
              <div>
                <label>Estado</label>
                <select value={form.estado} onChange={e => setForm({ ...form, estado: e.target.value })}>
                  <option value="PROGRAMADO">Programado</option>
                  <option value="EN_CURSO">En curso</option>
                  <option value="COMPLETADO">Completado</option>
                  <option value="CANCELADO">Cancelado</option>
                </select>
              </div>
              <div><label>Hora Inicio</label><input type="time" value={form.hora_inicio} onChange={e => setForm({ ...form, hora_inicio: e.target.value })} /></div>
              <div><label>Hora Fin</label><input type="time" value={form.hora_fin} onChange={e => setForm({ ...form, hora_fin: e.target.value })} /></div>
            </div>
            <div className="actions" style={{ marginTop: 20, justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setShow(false)}>Cancelar</button>
              <button className="btn-primary" onClick={save}>Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
