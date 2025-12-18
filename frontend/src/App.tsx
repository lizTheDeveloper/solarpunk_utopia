import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { OffersPage } from './pages/OffersPage'
import { NeedsPage } from './pages/NeedsPage'
import { CreateOfferPage } from './pages/CreateOfferPage'
import { CreateNeedPage } from './pages/CreateNeedPage'
import { ExchangesPage } from './pages/ExchangesPage'
import { DiscoveryPage } from './pages/DiscoveryPage'
import { KnowledgePage } from './pages/KnowledgePage'
import { NetworkPage } from './pages/NetworkPage'
import { AgentsPage} from './pages/AgentsPage'
import './App.css'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/offers" element={<OffersPage />} />
        <Route path="/offers/create" element={<CreateOfferPage />} />
        <Route path="/needs" element={<NeedsPage />} />
        <Route path="/needs/create" element={<CreateNeedPage />} />
        <Route path="/exchanges" element={<ExchangesPage />} />
        <Route path="/discovery" element={<DiscoveryPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/network" element={<NetworkPage />} />
        <Route path="/agents" element={<AgentsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
