import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import BrowseOffersPage from './pages/BrowseOffersPage'
import CreateOfferPage from './pages/CreateOfferPage'
import OfferDetailPage from './pages/OfferDetailPage'

function App() {
  return (
    <div className="app">
      <header>
        <div className="container">
          <h1>ValueFlows Node</h1>
          <p>Gift Economy Coordination for Solarpunk Communes</p>
        </div>
      </header>

      <div className="container">
        <nav>
          <Link to="/">Home</Link>
          <Link to="/browse">Browse Offers</Link>
          <Link to="/create">Create Offer</Link>
        </nav>

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/browse" element={<BrowseOffersPage />} />
          <Route path="/create" element={<CreateOfferPage />} />
          <Route path="/listing/:id" element={<OfferDetailPage />} />
        </Routes>
      </div>
    </div>
  )
}

export default App
