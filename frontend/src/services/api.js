import axios from 'axios';

// Endpoints generados al desplegar cada microservicio.
// Reemplazar tras `serverless deploy`.
export const API_URLS = {
  flota:      import.meta.env.VITE_API_FLOTA      || 'https://CHANGEME.execute-api.us-east-1.amazonaws.com/dev',
  conductores:import.meta.env.VITE_API_CONDUCTORES|| 'https://CHANGEME.execute-api.us-east-1.amazonaws.com/dev',
  horarios:   import.meta.env.VITE_API_HORARIOS   || 'https://CHANGEME.execute-api.us-east-1.amazonaws.com/dev',
  descansos:  import.meta.env.VITE_API_DESCANSOS  || 'https://CHANGEME.execute-api.us-east-1.amazonaws.com/dev',
  deudas:     import.meta.env.VITE_API_DEUDAS     || 'https://CHANGEME.execute-api.us-east-1.amazonaws.com/dev'
};

const make = (baseURL) => {
  const c = axios.create({ baseURL, timeout: 30000 });
  c.interceptors.response.use(
    r => r,
    e => {
      console.error('API error:', e?.response?.data || e.message);
      return Promise.reject(e);
    }
  );
  return c;
};

export const flotaApi       = make(API_URLS.flota);
export const conductoresApi = make(API_URLS.conductores);
export const horariosApi    = make(API_URLS.horarios);
export const descansosApi   = make(API_URLS.descansos);
export const deudasApi      = make(API_URLS.deudas);
