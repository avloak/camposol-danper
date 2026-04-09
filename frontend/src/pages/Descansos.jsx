import { useState } from 'react';
import { Link } from 'react-router-dom';
import { descansosApi } from '../services/api.js';
import ResultadosCsv from '../components/ResultadosCsv.jsx';

export default function Descansos() {
  const [form, setForm] = useState({
    instrucciones_s3: 's3://prontobus-descansos/instrucciones/extraer.md',
    contenido_s3: 's3://prontobus-descansos/certificados/',
    email: ''
  });
  const [running, setRunning] = useState(false);
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState(null);

  const start = async () => {
    setRunning(true); setResp(null); setErr(null);
    try {
      const r = await descansosApi.post('/descansos/workflow', form);
      setResp(r.data);
    } catch (e) {
      setErr(e?.response?.data?.error || 'Error iniciando workflow');
    } finally { setRunning(false); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">🏥 Procesamiento de Descansos Médicos</div>
          <Link to="/descansos/solicitudes">
            <button className="btn-secondary">📋 Ver Solicitudes para Aprobación</button>
          </Link>
        </div>
        <p style={{ color: '#666' }}>
          Workflow asíncrono que procesa certificados médicos en formato Markdown desde un bucket S3,
          extrae la información usando IA (Groq + Llama 3.3 70B), almacena resultados en DynamoDB,
          actualiza horarios afectados y envía un reporte CSV por correo. Cada certificado extraído
          genera automáticamente una <strong>solicitud PENDIENTE</strong> que el administrador debe
          aprobar o rechazar desde la pantalla de Solicitudes.
        </p>
      </div>

      <div className="card">
        <div className="card-title" style={{ fontSize: 16 }}>Iniciar Workflow</div>
        <div className="form-grid" style={{ marginTop: 16 }}>
          <div className="full">
            <label>Ruta S3 archivo de instrucciones (Markdown)</label>
            <input value={form.instrucciones_s3} onChange={e => setForm({ ...form, instrucciones_s3: e.target.value })} />
          </div>
          <div className="full">
            <label>Ruta S3 carpeta con certificados (Markdown)</label>
            <input value={form.contenido_s3} onChange={e => setForm({ ...form, contenido_s3: e.target.value })} />
          </div>
          <div className="full">
            <label>Correo destinatario del reporte</label>
            <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
          </div>
        </div>
        <div className="actions" style={{ marginTop: 16 }}>
          <button className="btn-primary" disabled={running} onClick={start}>
            {running ? 'Iniciando...' : 'Iniciar Workflow'}
          </button>
        </div>

        {err && <div className="alert alert-danger" style={{ marginTop: 16 }}>{err}</div>}
        {resp && (
          <div className="alert alert-success" style={{ marginTop: 16 }}>
            <strong>Workflow iniciado correctamente</strong>
            <pre style={{ marginTop: 8, fontSize: 12, whiteSpace: 'pre-wrap' }}>{JSON.stringify(resp, null, 2)}</pre>
          </div>
        )}
      </div>

      <ResultadosCsv
        api={descansosApi}
        basePath="/descansos"
        title="Resultados CSV - Descansos Médicos"
      />
    </div>
  );
}
