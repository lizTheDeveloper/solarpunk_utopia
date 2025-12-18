import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function BrowseOffers() {
  const [listings, setListings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    listing_type: 'offer',
    category: '',
  })

  useEffect(() => {
    loadListings()
  }, [filters])

  const loadListings = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.listing_type) params.append('listing_type', filters.listing_type)
      if (filters.category) params.append('category', filters.category)

      const response = await fetch(`/vf/listings/?${params}`)
      const data = await response.json()
      setListings(data.listings || [])
    } catch (err) {
      console.error('Failed to load listings:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="filters">
        <select
          value={filters.listing_type}
          onChange={(e) => setFilters({ ...filters, listing_type: e.target.value })}
        >
          <option value="">All</option>
          <option value="offer">Offers</option>
          <option value="need">Needs</option>
        </select>

        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
        >
          <option value="">All Categories</option>
          <option value="food">Food</option>
          <option value="tools">Tools</option>
          <option value="seeds">Seeds</option>
          <option value="skills">Skills</option>
          <option value="labor">Labor</option>
          <option value="knowledge">Knowledge</option>
        </select>

        <button onClick={loadListings} className="secondary">Refresh</button>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : listings.length === 0 ? (
        <div className="card">
          <p>No listings found. Be the first to create one!</p>
        </div>
      ) : (
        <div className="listing-grid">
          {listings.map(listing => (
            <Link key={listing.id} to={`/listing/${listing.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className={`listing-card ${listing.listing_type}`}>
                <div className="badge ${listing.listing_type}">
                  {listing.listing_type}
                </div>
                <h3>{listing.title || 'Untitled'}</h3>
                <div className="meta">
                  {listing.quantity} {listing.unit}
                </div>
                {listing.description && (
                  <div className="description">{listing.description}</div>
                )}
                <div className="meta">
                  Status: {listing.status}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default BrowseOffers
