import { FrappeProvider } from 'frappe-react-sdk'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import PageNotFound from './components/common/PageNotFound/PageNotFound'
import CreateERD from './pages/features/erd/meta/CreateERDForMeta'

function App() {
  const getSiteName = () => {
    // @ts-ignore
    if (window.frappe?.boot?.versions?.frappe && (window.frappe.boot.versions.frappe.startsWith('15') || window.frappe.boot.versions.frappe.startsWith('16'))) {
      // @ts-ignore
      return window.frappe?.boot?.sitename ?? import.meta.env.VITE_SITE_NAME
    }
    return import.meta.env.VITE_SITE_NAME
  }

  return (
    <FrappeProvider socketPort={import.meta.env.VITE_SOCKET_PORT ?? undefined} siteName={getSiteName()}>
      <BrowserRouter basename={import.meta.env.VITE_BASE_PATH}>
        <Routes>
          <Route path="/" element={<CreateERD />} />
          <Route path="/meta-erd/create" element={<CreateERD />} />
          <Route path="/404" element={<PageNotFound />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </FrappeProvider>
  )
}

export default App
