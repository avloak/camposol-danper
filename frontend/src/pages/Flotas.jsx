import { useEffect, useState } from 'react';
import { flotaApi } from '../services/api.js';

const empty = {
  placa: '', marca: '', modelo: '', anio: '', capacidad: '',
  soat_vencimiento: '', revision_tecnica_vencimiento: '', estado: 'OPERATIVO'
};

function diffDays(date) {
  if (!date) return null;
  const d = new Date(date);
  return Math.ceil((d - new Date()) / 86400000);
}

function badgeFor(date) {
  const d = diffDays(date);
  if (d === null) return null;
  if (d < 0)   return <span className="badge badge-danger">Vencido</span>;
  if (d <= 30) return <span className="badge badge-warning">{d}d</span>;
  return <span className="badge badge-success">{d}d</span>;
}

export default function Flotas() {
  const [items, setItems] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await flotaApi.get('/buses');
      setItems(r.data?.items || r.data || []);
    } catch (e) {
      setMsg({ type: 'danger', text: 'Error cargando buses' });
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openNew = () => { setForm(empty); setEditingId(null); setShow(true); };
  const openEdit = (b) => { setForm({ ...empty, ...b }); setEditingId(b.id); setShow(true); };

  const save = async () => {
    try {
      if (editingId) {
        await flotaApi.put(`/buses/${editingId}`, form);
        setMsg({ type: 'success', text: 'Bus actualizado' });
      } else {
        await flotaApi.post('/buses', form);
        setMsg({ type: 'success', text: 'Bus creado' });
      }
      setShow(false);
      load();
    } catch (e) {
      setMsg({ type: 'danger', text: 'Error al guardar' });
    }
  };

  const remove = async (id) => {
    if (!confirm('¿Eliminar este bus?')) return;
    try {
      await flotaApi.delete(`/buses/${id}`);
      load();
    } catch (e) { setMsg({ type: 'danger', text: 'Error al eliminar' }); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">🚌 Gestión de Flota</div>
          <button className="btn-primary" onClick={openNew}>+ Nuevo Bus</button>
        </div>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {loading ? <div className="empty">Cargando...</div> :
          items.length === 0 ? <div className="empty">Sin buses registrados</div> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Placa</th><th>Marca</th><th>Modelo</th><th>Año</th>
                  <th>SOAT</th><th>Rev. Téc.</th><th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map(b => (
                  <tr key={b.id}>
                    <td><strong>{b.placa}</strong></td>
                    <td>{b.marca}</td>
                    <td>{b.modelo}</td>
                    <td>{b.anio}</td>
                    <td>{badgeFor(b.soat_vencimiento)}</td>
                    <td>{badgeFor(b.revision_tecnica_vencimiento)}</td>
                    <td>{b.estado}</td>
                    <td className="actions">
                      <button className="btn-secondary" onClick={() => openEdit(b)}>Editar</button>
                      <button className="btn-danger" onClick={() => remove(b.id)}>Eliminar</button>
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
            <h3 style={{ marginBottom: 16 }}>{editingId ? 'Editar Bus' : 'Nuevo Bus'}</h3>
            <div className="form-grid">
              <div><label>Placa</label><input value={form.placa} onChange={e => setForm({ ...form, placa: e.target.value })} /></div>
              <div><label>Marca</label><input value={form.marca} onChange={e => setForm({ ...form, marca: e.target.value })} /></div>
              <div><label>Modelo</label><input value={form.modelo} onChange={e => setForm({ ...form, modelo: e.target.value })} /></div>
              <div><label>Año</label><input type="number" value={form.anio} onChange={e => setForm({ ...form, anio: e.target.value })} /></div>
              <div><label>Capacidad (pasajeros)</label><input type="number" value={form.capacidad} onChange={e => setForm({ ...form, capacidad: e.target.value })} /></div>
              <div>
                <label>Estado</label>
                <select value={form.estado} onChange={e => setForm({ ...form, estado: e.target.value })}>
                  <option value="OPERATIVO">Operativo</option>
                  <option value="MANTENIMIENTO">Mantenimiento</option>
                  <option value="INACTIVO">Inactivo</option>
                </select>
              </div>
              <div><label>Vencimiento SOAT</label><input type="date" value={form.soat_vencimiento} onChange={e => setForm({ ...form, soat_vencimiento: e.target.value })} /></div>
              <div><label>Vencimiento Rev. Técnica</label><input type="date" value={form.revision_tecnica_vencimiento} onChange={e => setForm({ ...form, revision_tecnica_vencimiento: e.target.value })} /></div>
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
