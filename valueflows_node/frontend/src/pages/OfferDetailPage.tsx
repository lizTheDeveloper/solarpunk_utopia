import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'

function OfferDetailPage() {
  const { id } = useParams()
  const [listing, setListing] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetch(`/vf/listings/${id}`)
        .then(res => res.json())
        .then(data => {
          setListing(data)
          setLoading(false)
        })
        .catch(err => {
          console.error('Failed to load listing:', err)
          setLoading(false)
        })
    }
  }, [id])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!listing) {
    return (
      <div className="card">
        <p>Listing not found.</p>
        <Link to="/browse"><button>Back to Browse</button></Link>
      </div>
    )
  }

  return (
    <div>
      <div className="card">
        <div className={`badge ${listing.listing_type}`}>
          {listing.listing_type}
        </div>
        <h2>{listing.title || 'Untitled Listing'}</h2>

        <div style={{ marginTop: '20px' }}>
          <p><strong>Quantity:</strong> {listing.quantity} {listing.unit}</p>
          <p><strong>Status:</strong> {listing.status}</p>

          {listing.description && (
            <div style={{ marginTop: '15px' }}>
              <strong>Description:</strong>
              <p>{listing.description}</p>
            </div>
          )}

          {listing.available_from && (
            <p><strong>Available from:</strong> {new Date(listing.available_from).toLocaleDateString()}</p>
          )}

          {listing.available_until && (
            <p><strong>Available until:</strong> {new Date(listing.available_until).toLocaleDateString()}</p>
          )}
        </div>

        <div style={{ marginTop: '30px', display: 'flex', gap: '10px' }}>
          <button>Create Match</button>
          <Link to="/browse"><button className="secondary">Back to Browse</button></Link>
        </div>
      </div>
    </div>
  )
}

export default OfferDetailPage
