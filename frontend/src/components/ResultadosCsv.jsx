import { useEffect, useState } from 'react';

/**
 * Componente reutilizable que lista los CSVs de /resultados/ del bucket S3
 * del microservicio indicado y permite descargarlos directamente desde el navegador.
 *
 * Props:
 *   api         → cliente axios (descansosApi | deudasApi)
 *   basePath    → '/descansos' | '/deudas'
 *   title       → título del card
 */
export default function ResultadosCsv({ api, basePath, title = 'Resultados CSV' }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null);
  const [err, setErr] = useState(null);

  const load = async () => {
    setLoading(true); setErr(null);
    try {
      const r = await api.get(`${basePath}/resultados`);
      setItems(r.data?.items || []);
    } catch (e) {
      setErr(e?.response?.data?.error || 'Error listando resultados');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const download = async (item) => {
    setDownloading(item.key);
    try {
      // pedimos presigned URL y el navegador baja el archivo
      const r = await api.get(`${basePath}/resultados/download/${encodeURIComponent(item.key)}`);
      const url = r.data?.url;
      if (!url) throw new Error('No se obtuvo URL');
      // Forzamos la descarga con un <a> temporal
      const a = document.createElement('a');
      a.href = url;
      a.download = item.filename;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (e) {
      setErr(e?.response?.data?.error || e.message || 'Error descargando archivo');
    } finally { setDownloading(null); }
  };

  const fmtSize = (b) => {
    if (!b) return '—';
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / 1024 / 1024).toFixed(2)} MB`;
  };

  const fmtDate = (iso) => {
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title" style={{ fontSize: 16 }}>📥 {title}</div>
        <button className="btn-secondary" onClick={load} disabled={loading}>
          {loading ? 'Cargando...' : '↻ Refrescar'}
        </button>
      </div>

      <p style={{ color: '#666', fontSize: 13, marginBottom: 12 }}>
        Listado de archivos CSV generados por el workflow IA y almacenados en
        <code style={{ background: '#f1f3f5', padding: '2px 6px', borderRadius: 4, marginLeft: 4 }}>
          s3://{basePath.replace('/', '')}/resultados/
        </code>. Haz clic en <strong>Descargar</strong> para obtener el archivo.
      </p>

      {err && <div className="alert alert-danger">{err}</div>}

      {loading ? <div className="empty">Cargando...</div> :
        items.length === 0 ? (
          <div className="empty">Aún no hay resultados. Ejecuta un workflow primero.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Archivo</th>
                  <th>Tamaño</th>
                  <th>Generado</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {items.map(it => (
                  <tr key={it.key}>
                    <td>
                      <div style={{ fontFamily: 'monospace', fontSize: 13 }}>📄 {it.filename}</div>
                    </td>
                    <td>{fmtSize(it.size)}</td>
                    <td>{fmtDate(it.last_modified)}</td>
                    <td>
                      <button
                        className="btn-primary"
                        disabled={downloading === it.key}
                        onClick={() => download(it)}
                      >
                        {downloading === it.key ? 'Descargando...' : '⬇ Descargar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </div>
  );
}
