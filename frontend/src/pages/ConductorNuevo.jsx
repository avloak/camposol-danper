import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { conductoresApi } from '../services/api.js';

const STEPS = [
  'Datos personales',
  'Licencia',
  'Legajo',
  'Disponibilidad'
];

const empty = {
  // paso 1
  dni: '', nombre: '', apellidos: '', fecha_nacimiento: '', telefono: '', email: '', direccion: '',
  // paso 2
  licencia_numero: '', licencia_categoria: 'A-IIb', licencia_emision: '', licencia_vencimiento: '',
  // paso 3
  fecha_ingreso: '', cargo: 'Conductor', salario: '', contacto_emergencia: '', contacto_emergencia_telefono: '',
  // paso 4
  disponibilidad: 'DISPONIBLE', observaciones: ''
};

export default function ConductorNuevo() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const next = () => setStep(s => Math.min(STEPS.length - 1, s + 1));
  const prev = () => setStep(s => Math.max(0, s - 1));

  const submit = async () => {
    setSaving(true); setErr(null);
    try {
      await conductoresApi.post('/conductores', form);
      nav('/conductores');
    } catch (e) {
      setErr('Error guardando conductor');
    } finally { setSaving(false); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">Nuevo Conductor</div>
          <button className="btn-secondary" onClick={() => nav('/conductores')}>Cancelar</button>
        </div>

        <div className="steps">
          {STEPS.map((s, i) => (
            <div key={s} className={`step ${i === step ? 'active' : i < step ? 'done' : ''}`}>
              {i + 1}. {s}
            </div>
          ))}
        </div>

        {err && <div className="alert alert-danger">{err}</div>}

        {step === 0 && (
          <div className="form-grid">
            <div><label>DNI</label><input value={form.dni} onChange={e => set('dni', e.target.value)} /></div>
            <div><label>Nombre</label><input value={form.nombre} onChange={e => set('nombre', e.target.value)} /></div>
            <div><label>Apellidos</label><input value={form.apellidos} onChange={e => set('apellidos', e.target.value)} /></div>
            <div><label>Fecha de Nacimiento</label><input type="date" value={form.fecha_nacimiento} onChange={e => set('fecha_nacimiento', e.target.value)} /></div>
            <div><label>Teléfono</label><input value={form.telefono} onChange={e => set('telefono', e.target.value)} /></div>
            <div><label>Email</label><input type="email" value={form.email} onChange={e => set('email', e.target.value)} /></div>
            <div className="full"><label>Dirección</label><input value={form.direccion} onChange={e => set('direccion', e.target.value)} /></div>
          </div>
        )}

        {step === 1 && (
          <div className="form-grid">
            <div><label>Número de Licencia</label><input value={form.licencia_numero} onChange={e => set('licencia_numero', e.target.value)} /></div>
            <div>
              <label>Categoría</label>
              <select value={form.licencia_categoria} onChange={e => set('licencia_categoria', e.target.value)}>
                <option>A-I</option><option>A-IIa</option><option>A-IIb</option>
                <option>A-IIIa</option><option>A-IIIb</option><option>A-IIIc</option>
              </select>
            </div>
            <div><label>Fecha de Emisión</label><input type="date" value={form.licencia_emision} onChange={e => set('licencia_emision', e.target.value)} /></div>
            <div><label>Fecha de Vencimiento</label><input type="date" value={form.licencia_vencimiento} onChange={e => set('licencia_vencimiento', e.target.value)} /></div>
          </div>
        )}

        {step === 2 && (
          <div className="form-grid">
            <div><label>Fecha de Ingreso</label><input type="date" value={form.fecha_ingreso} onChange={e => set('fecha_ingreso', e.target.value)} /></div>
            <div><label>Cargo</label><input value={form.cargo} onChange={e => set('cargo', e.target.value)} /></div>
            <div><label>Salario</label><input type="number" value={form.salario} onChange={e => set('salario', e.target.value)} /></div>
            <div><label>Contacto Emergencia</label><input value={form.contacto_emergencia} onChange={e => set('contacto_emergencia', e.target.value)} /></div>
            <div className="full"><label>Tel. Emergencia</label><input value={form.contacto_emergencia_telefono} onChange={e => set('contacto_emergencia_telefono', e.target.value)} /></div>
          </div>
        )}

        {step === 3 && (
          <div className="form-grid">
            <div>
              <label>Disponibilidad</label>
              <select value={form.disponibilidad} onChange={e => set('disponibilidad', e.target.value)}>
                <option value="DISPONIBLE">Disponible</option>
                <option value="ASIGNADO">Asignado</option>
                <option value="DESCANSO">En descanso</option>
                <option value="VACACIONES">Vacaciones</option>
              </select>
            </div>
            <div className="full"><label>Observaciones</label><textarea rows="4" value={form.observaciones} onChange={e => set('observaciones', e.target.value)} /></div>
          </div>
        )}

        <div className="actions" style={{ marginTop: 20, justifyContent: 'space-between' }}>
          <button className="btn-secondary" onClick={prev} disabled={step === 0}>← Anterior</button>
          {step < STEPS.length - 1
            ? <button className="btn-primary" onClick={next}>Siguiente →</button>
            : <button className="btn-success" onClick={submit} disabled={saving}>{saving ? 'Guardando...' : 'Crear Conductor'}</button>}
        </div>
      </div>
    </div>
  );
}
