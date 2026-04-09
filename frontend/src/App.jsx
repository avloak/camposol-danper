import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Flotas from './pages/Flotas.jsx';
import Conductores from './pages/Conductores.jsx';
import ConductorNuevo from './pages/ConductorNuevo.jsx';
import Horarios from './pages/Horarios.jsx';
import Descansos from './pages/Descansos.jsx';
import SolicitudesDescanso from './pages/SolicitudesDescanso.jsx';
import Deudas from './pages/Deudas.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="flotas" element={<Flotas />} />
        <Route path="conductores" element={<Conductores />} />
        <Route path="conductores/nuevo" element={<ConductorNuevo />} />
        <Route path="horarios" element={<Horarios />} />
        <Route path="descansos" element={<Descansos />} />
        <Route path="descansos/solicitudes" element={<SolicitudesDescanso />} />
        <Route path="deudas" element={<Deudas />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
