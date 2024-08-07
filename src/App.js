import React, { useState, useEffect } from 'react';
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Route, Routes, useLocation } from "react-router-dom";
import { ColorModeContext, useMode } from "./theme";
import Navbar from "./global/navbar";
import SidebarComponent from "./global/Sidebar";
import Principal from "./pages/principal";
import PProducto from "./pages/productos";
import Carrito from "./pages/carrito";
import Crud from "./pages/crud";
import Registro from "./pages/registro";
import Login from "./pages/login";
import Perfil from "./pages/perfil";
import Empleados from "./pages/administracion/empleados";
import Envios from "./pages/administracion/envios";
import Inventario from "./pages/administracion/inventario";
import Pedidos from "./pages/administracion/pedidos";
import Reportes from "./pages/administracion/reportes";
import Usuarios from "./pages/administracion/usuarios";
import Show from "./components/Show";
import Edit from "./components/Edit";
import Create from "./components/Create";
import DetalleProducto from './pages/detalleproducto';
import UserContext from '../src/components/UserContext';
import { AuthProvider } from '../src/components/AuthContext';
import Footer from "./global/Footer"; 

function App() {
  const [userEmail, setUserEmail] = useState(null);
  const [theme, colorMode] = useMode();
  const [selectedCurrency, setSelectedCurrency] = useState(localStorage.getItem('selectedCurrency') || 'Peso');
  const [valorGeneral, setValorGeneral] = useState(parseFloat(localStorage.getItem('valorGeneral')) || 1);

  const location = useLocation();
  
  const handleCurrencyChange = (currency, value) => {
    setSelectedCurrency(currency);
    setValorGeneral(value);
    localStorage.setItem('selectedCurrency', currency);
    localStorage.setItem('valorGeneral', value.toString());
  };

  useEffect(() => {
    const storedCurrency = localStorage.getItem('selectedCurrency');
    const storedValue = localStorage.getItem('valorGeneral');
    if (storedCurrency && storedValue) {
      setSelectedCurrency(storedCurrency);
      setValorGeneral(parseFloat(storedValue));
    }
  }, []);

  const shouldDisplaySidebar = () => {
    const routesWithSidebar = [
      '/usuarios',
      '/empleados',
      '/inventario',
      '/pedidos',
      '/envios',
      '/reportes'
    ];
    return routesWithSidebar.includes(location.pathname);
  };

  return (
    <AuthProvider>
      <UserContext.Provider value={userEmail}>
        <ColorModeContext.Provider value={colorMode}>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <div className="app" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <Navbar onCurrencyChange={handleCurrencyChange} />
              <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
                {shouldDisplaySidebar() && <SidebarComponent />}
                <main className="content" style={{ flex: 1, marginLeft: shouldDisplaySidebar() ? '1px' : '0', transition: 'margin-left 0.3s' }}>
                  <Routes>
                    <Route path="/" element={<Principal selectedCurrency={selectedCurrency} valorGeneral={valorGeneral} />} />
                    <Route path="/PProducto" element={<PProducto />} />
                    <Route path="/carrito" element={<Carrito />} />
                    <Route path="/crud" element={<Crud />} /> 
                    <Route path="/empleados" element={<Empleados />} />
                    <Route path="/envios" element={<Envios />} />
                    <Route path="/inventario" element={<Inventario />} />
                    <Route path="/pedidos" element={<Pedidos />} />
                    <Route path="/reportes" element={<Reportes />} />
                    <Route path="/usuarios" element={<Usuarios />} />
                    <Route path="/show" element={<Show />} />
                    <Route path="/edit/:id" element={<Edit />} />
                    <Route path="/create" element={<Create />} />
                    <Route path="/registro" element={<Registro />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/perfil" element={<Perfil />} />
                    <Route path="/product/:productId" element={<DetalleProducto />} /> 
                  </Routes>
                </main>
              </div>
              <Footer /> 
            </div>
          </ThemeProvider>
        </ColorModeContext.Provider>
      </UserContext.Provider>
    </AuthProvider>
  );
}

export default App;
