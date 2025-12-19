import { Routes, Route } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { CommunityProvider } from './contexts/CommunityContext'
import { Layout } from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
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
import { EventCreatePage } from './pages/EventCreatePage'
import { EventJoinPage } from './pages/EventJoinPage'
import { CellsPage } from './pages/CellsPage'
import { CellDetailPage } from './pages/CellDetailPage'
import { CreateCellPage } from './pages/CreateCellPage'
import { MessagesPage } from './pages/MessagesPage'
import { MessageThreadPage } from './pages/MessageThreadPage'
import { NewMessagePage } from './pages/NewMessagePage'
import './App.css'

// Import API interceptors to add auth token to requests
import './api/interceptors'

// Import local storage initialization
import { initializeStorage } from './api/adaptive-valueflows'

function App() {
  const [storageReady, setStorageReady] = useState(false);

  useEffect(() => {
    // Initialize local SQLite database for offline-first operation
    initializeStorage()
      .then(() => {
        setStorageReady(true);
        console.log('App storage initialized');
      })
      .catch(error => {
        console.error('Failed to initialize storage:', error);
        // Continue anyway - app can still work with remote API
        setStorageReady(true);
      });
  }, []);

  if (!storageReady) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.2rem'
      }}>
        Initializing local storage...
      </div>
    );
  }

  return (
    <AuthProvider>
      <CommunityProvider>
        <Routes>
          {/* Public route - no auth needed */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes - require auth */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
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
                    <Route path="/events/create" element={<EventCreatePage />} />
                    <Route path="/join/event/:inviteCode" element={<EventJoinPage />} />
                    <Route path="/join/event" element={<EventJoinPage />} />
                    <Route path="/cells" element={<CellsPage />} />
                    <Route path="/cells/create" element={<CreateCellPage />} />
                    <Route path="/cells/:cellId" element={<CellDetailPage />} />
                    <Route path="/messages" element={<MessagesPage />} />
                    <Route path="/messages/new" element={<NewMessagePage />} />
                    <Route path="/messages/:threadId" element={<MessageThreadPage />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </CommunityProvider>
    </AuthProvider>
  )
}

export default App
