import { useState } from 'react';
import { deudasApi } from '../services/api.js';
import ResultadosCsv from '../components/ResultadosCsv.jsx';

export default function Deudas() {
  const [form, setForm] = useState({
    instrucciones_s3: 's3://prontobus-deudas/instrucciones/extraer.md',
    contenido_s3: 's3://prontobus-deudas/infracciones/',
    email: ''
  });
  const [running, setRunning] = useState(false);
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState(null);

  const start = async () => {
    setRunning(true); setResp(null); setErr(null);
    try {
      const r = await deudasApi.post('/deudas/workflow', form);
      setResp(r.data);
    } catch (e) {
      setErr(e?.response?.data?.error || 'Error iniciando workflow');
    } finally { setRunning(false); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-title">💰 Procesamiento de Deudas por Infracciones</div>
        <p style={{ marginTop: 8, color: '#666' }}>
          Workflow asíncrono que procesa documentos de infracciones en formato Markdown,
          extrae deudas con IA, calcula fechas límite de descuento, genera el ranking de infractores
          y envía un reporte CSV por correo.
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
            <label>Ruta S3 carpeta con documentos de infracciones</label>
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
        api={deudasApi}
        basePath="/deudas"
        title="Resultados CSV - Deudas / Infracciones"
      />
    </div>
  );
}
