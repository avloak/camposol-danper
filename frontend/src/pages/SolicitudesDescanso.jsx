import { useEffect, useState } from 'react';
import { descansosApi, API_URLS } from '../services/api.js';

const ESTADOS = ['PENDIENTE', 'APROBADO', 'RECHAZADO'];

const empty = {
  paciente_nombre: '', paciente_dni: '',
  medico_nombre: '', medico_cmp: '',
  diagnostico: '',
  fecha_inicio: '', fecha_fin: '',
  remitente_nombre: '', remitente_email: '',
  conductor_id: ''
};

function badge(estado) {
  const map = {
    PENDIENTE: 'badge-warning',
    APROBADO:  'badge-success',
    RECHAZADO: 'badge-danger'
  };
  return <span className={`badge ${map[estado] || ''}`}>{estado}</span>;
}

export default function SolicitudesDescanso() {
  const [items, setItems] = useState([]);
  const [filtro, setFiltro] = useState('PENDIENTE');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);

  const [selected, setSelected] = useState(null);
  const [obs, setObs] = useState('');
  const [acting, setActing] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const url = filtro ? `/descansos/solicitudes?estado=${filtro}` : '/descansos/solicitudes';
      const r = await descansosApi.get(url);
      setItems(r.data?.items || []);
    } catch (e) {
      setMsg({ type: 'danger', text: 'Error cargando solicitudes' });
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filtro]);

  const crearManual = async () => {
    setSaving(true);
    try {
      await descansosApi.post('/descansos/solicitudes', { ...form, origen: 'MANUAL' });
      setShowNew(false);
      setForm(empty);
      setFiltro('PENDIENTE');
      setMsg({ type: 'success', text: 'Solicitud registrada' });
      load();
    } catch (e) {
      setMsg({ type: 'danger', text: e?.response?.data?.error || 'Error al guardar' });
    } finally { setSaving(false); }
  };

  const exportarCsv = async () => {
    setExporting(true);
    try {
      const url = filtro
        ? `${API_URLS.descansos}/descansos/solicitudes/exportar?estado=${filtro}`
        : `${API_URLS.descansos}/descansos/solicitudes/exportar`;
      // Descargamos como blob y forzamos el download
      const r = await descansosApi.get(
        filtro ? `/descansos/solicitudes/exportar?estado=${filtro}` : '/descansos/solicitudes/exportar',
        { responseType: 'blob' }
      );
      const blob = new Blob([r.data], { type: 'text/csv;charset=utf-8' });
      const href = URL.createObjectURL(blob);
      const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
      const sufijo = filtro ? `-${filtro.toLowerCase()}` : '';
      const a = document.createElement('a');
      a.href = href;
      a.download = `solicitudes-descansos${sufijo}-${ts}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(href);
      setMsg({ type: 'success', text: 'CSV descargado correctamente' });
    } catch (e) {
      setMsg({ type: 'danger', text: 'Error exportando CSV' });
      // fallback por si el navegador maneja la content-disposition
      // window.open(url, '_blank');
    } finally { setExporting(false); }
  };

  const accion = async (tipo) => {
    if (!selected) return;
    setActing(true);
    try {
      const ruta = tipo === 'APROBADO' ? 'aprobar' : 'rechazar';
      const r = await descansosApi.put(
        `/descansos/solicitudes/${selected.id}/${ruta}`,
        { observaciones: obs, revisado_por: 'admin' }
      );
      setMsg({
        type: 'success',
        text: `Solicitud ${tipo}. Email enviado: ${r.data?.email?.status || 'N/D'}`
      });
      setSelected(null);
      setObs('');
      load();
    } catch (e) {
      setMsg({ type: 'danger', text: e?.response?.data?.error || 'Error al procesar' });
    } finally { setActing(false); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">🏥 Solicitudes de Descanso Médico</div>
          <div className="actions">
            <select value={filtro} onChange={e => setFiltro(e.target.value)} style={{ width: 'auto' }}>
              <option value="">Todos</option>
              {ESTADOS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button className="btn-secondary" onClick={exportarCsv} disabled={exporting}>
              {exporting ? 'Exportando...' : '⬇ Exportar CSV'}
            </button>
            <button className="btn-primary" onClick={() => setShowNew(true)}>+ Nueva Solicitud</button>
          </div>
        </div>

        <p style={{ color: '#666', marginBottom: 16 }}>
          Listado de descansos médicos extraídos por la IA o ingresados manualmente.
          El administrador puede aprobar o rechazar cada solicitud; al hacerlo se envía
          automáticamente un correo al remitente vía SendGrid.
        </p>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {loading ? <div className="empty">Cargando...</div> :
          items.length === 0 ? <div className="empty">Sin solicitudes</div> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Paciente</th><th>DNI</th><th>Médico</th><th>CMP</th>
                  <th>Diagnóstico</th><th>Desde</th><th>Hasta</th><th>Días</th>
                  <th>Origen</th><th>Estado</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map(s => (
                  <tr key={s.id}>
                    <td><strong>{s.paciente_nombre}</strong></td>
                    <td>{s.paciente_dni}</td>
                    <td>{s.medico_nombre}</td>
                    <td>{s.medico_cmp}</td>
                    <td title={s.diagnostico} style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {s.diagnostico}
                    </td>
                    <td>{s.fecha_inicio}</td>
                    <td>{s.fecha_fin}</td>
                    <td>{s.dias_descanso}</td>
                    <td><span className="badge" style={{ background: '#e9ecef', color: '#444' }}>{s.origen}</span></td>
                    <td>{badge(s.estado)}</td>
                    <td className="actions">
                      <button className="btn-secondary" onClick={() => { setSelected(s); setObs(s.observaciones || ''); }}>
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ----- Modal Crear Solicitud Manual ----- */}
      {showNew && (
        <div className="modal-bg" onClick={() => setShowNew(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 16 }}>Nueva Solicitud de Descanso Médico</h3>
            <div className="form-grid">
              <div><label>Nombre del Paciente</label><input value={form.paciente_nombre} onChange={e => setForm({ ...form, paciente_nombre: e.target.value })} /></div>
              <div><label>DNI del Paciente</label><input value={form.paciente_dni} onChange={e => setForm({ ...form, paciente_dni: e.target.value })} /></div>
              <div><label>Nombre del Médico</label><input value={form.medico_nombre} onChange={e => setForm({ ...form, medico_nombre: e.target.value })} /></div>
              <div><label>CMP del Médico</label><input value={form.medico_cmp} onChange={e => setForm({ ...form, medico_cmp: e.target.value })} placeholder="Ej. 12345" /></div>
              <div className="full"><label>Diagnóstico</label><textarea rows="2" value={form.diagnostico} onChange={e => setForm({ ...form, diagnostico: e.target.value })} /></div>
              <div><label>Fecha Inicio</label><input type="date" value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} /></div>
              <div><label>Fecha Fin</label><input type="date" value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} /></div>
              <div><label>Conductor (ID)</label><input value={form.conductor_id} onChange={e => setForm({ ...form, conductor_id: e.target.value })} /></div>
              <div><label>Remitente (nombre)</label><input value={form.remitente_nombre} onChange={e => setForm({ ...form, remitente_nombre: e.target.value })} /></div>
              <div className="full"><label>Remitente (email)</label><input type="email" value={form.remitente_email} onChange={e => setForm({ ...form, remitente_email: e.target.value })} /></div>
            </div>
            <div className="actions" style={{ marginTop: 20, justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setShowNew(false)}>Cancelar</button>
              <button className="btn-primary" disabled={saving} onClick={crearManual}>{saving ? 'Guardando...' : 'Registrar'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ----- Modal Detalle / Aprobar / Rechazar ----- */}
      {selected && (
        <div className="modal-bg" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 4 }}>Solicitud de Descanso Médico</h3>
            <div style={{ marginBottom: 16 }}>{badge(selected.estado)}</div>

            <div className="form-grid">
              <div><label>Paciente</label><input value={selected.paciente_nombre} disabled /></div>
              <div><label>DNI</label><input value={selected.paciente_dni} disabled /></div>
              <div><label>Médico</label><input value={selected.medico_nombre} disabled /></div>
              <div><label>CMP</label><input value={selected.medico_cmp} disabled /></div>
              <div className="full"><label>Diagnóstico</label><textarea rows="2" value={selected.diagnostico} disabled /></div>
              <div><label>Fecha Inicio</label><input value={selected.fecha_inicio} disabled /></div>
              <div><label>Fecha Fin</label><input value={selected.fecha_fin} disabled /></div>
              <div><label>Días</label><input value={selected.dias_descanso} disabled /></div>
              <div><label>Origen</label><input value={selected.origen} disabled /></div>
              <div className="full"><label>Remitente</label><input value={`${selected.remitente_nombre || ''} <${selected.remitente_email || ''}>`} disabled /></div>
              {selected.archivo_origen && (
                <div className="full"><label>Archivo origen</label><input value={selected.archivo_origen} disabled /></div>
              )}
              <div className="full">
                <label>Observaciones (se incluirán en el correo)</label>
                <textarea rows="3" value={obs} onChange={e => setObs(e.target.value)} disabled={selected.estado !== 'PENDIENTE'} />
              </div>
            </div>

            <div className="actions" style={{ marginTop: 20, justifyContent: 'space-between' }}>
              <button className="btn-secondary" onClick={() => setSelected(null)}>Cerrar</button>
              {selected.estado === 'PENDIENTE' && (
                <div className="actions">
                  <button className="btn-danger" disabled={acting} onClick={() => accion('RECHAZADO')}>
                    {acting ? '...' : '✕ Rechazar y enviar correo'}
                  </button>
                  <button className="btn-success" disabled={acting} onClick={() => accion('APROBADO')}>
                    {acting ? '...' : '✓ Aprobar y enviar correo'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
