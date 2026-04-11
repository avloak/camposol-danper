import { useState, useRef } from 'react';
import { deudasApi } from '../services/api.js';
import ResultadosCsv from '../components/ResultadosCsv.jsx';

const PDF_S3_BASE = import.meta.env.VITE_DEUDAS_PDF_S3 || 's3://ms-deudas-dev-bucket-985495523801/pdfs/';

export default function Deudas() {
  const [form, setForm] = useState({
    instrucciones_s3: import.meta.env.VITE_DEUDAS_INSTRUCCIONES_S3 || '',
    contenido_s3: import.meta.env.VITE_DEUDAS_CONTENIDO_S3 || '',
    email: ''
  });
  const [running, setRunning] = useState(false);
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState(null);

  // PDF upload state
  const [pdfFiles, setPdfFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [uploadErr, setUploadErr] = useState(null);
  const fileInputRef = useRef(null);

  const start = async () => {
    setRunning(true); setResp(null); setErr(null);
    try {
      const r = await deudasApi.post('/deudas/workflow', form);
      setResp(r.data);
    } catch (e) {
      setErr(e?.response?.data?.error || 'Error iniciando workflow');
    } finally { setRunning(false); }
  };

  const onFilesChange = (e) => {
    const selected = Array.from(e.target.files).filter(f => f.type === 'application/pdf');
    setPdfFiles(selected);
    setUploadResults([]);
    setUploadErr(null);
  };

  const readAsBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const uploadPdfs = async () => {
    if (!pdfFiles.length) return;
    setUploading(true); setUploadResults([]); setUploadErr(null);

    const results = [];
    for (const file of pdfFiles) {
      try {
        const content = await readAsBase64(file);
        const { data } = await deudasApi.post('/deudas/upload-url', {
          filename: file.name,
          content,
        });
        results.push({ name: file.name, s3_uri: data.s3_uri, ok: true });
      } catch (e) {
        const msg = e?.response?.data?.error || e.message;
        results.push({ name: file.name, error: msg, ok: false });
      }
    }

    setUploadResults(results);
    setUploading(false);
    setPdfFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
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

      {/* PDF Upload */}
      <div className="card">
        <div className="card-title" style={{ fontSize: 16 }}>📄 Subir PDFs al Bucket S3</div>
        <p style={{ marginTop: 4, marginBottom: 12, color: '#666', fontSize: 13 }}>
          Destino: <code>{PDF_S3_BASE}</code>
        </p>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            multiple
            onChange={onFilesChange}
          />
          <button
            className="btn-primary"
            disabled={uploading || !pdfFiles.length}
            onClick={uploadPdfs}
          >
            {uploading ? 'Subiendo...' : `Subir ${pdfFiles.length ? `(${pdfFiles.length})` : ''}`}
          </button>
        </div>

        {uploadErr && <div className="alert alert-danger" style={{ marginTop: 12 }}>{uploadErr}</div>}

        {uploadResults.length > 0 && (
          <div style={{ marginTop: 12 }}>
            {uploadResults.map((r, i) => (
              <div
                key={i}
                className={`alert ${r.ok ? 'alert-danger' : 'alert-success'}`}
                style={{ marginBottom: 6, padding: '8px 12px', fontSize: 13 }}
              >
                {r.ok
                  ? <span>❌ <strong>{r.name}</strong>: {r.error}</span>
                  : <span>✅ <strong>{r.name}</strong> → <code>{PDF_S3_BASE}</code></span>
                }
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Workflow */}
      <div className="card">
        <div className="card-title" style={{ fontSize: 16 }}>Iniciar Workflow</div>
        <div className="form-grid" style={{ marginTop: 16 }}>
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
