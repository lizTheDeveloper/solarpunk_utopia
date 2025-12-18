import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

function HomePage() {
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    fetch('/vf/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Failed to load stats:', err))
  }, [])

  return (
    <div>
      <div className="card">
        <h2>Welcome to ValueFlows Node</h2>
        <p>
          This is your local gift economy coordination system. Share resources,
          coordinate exchanges, and build community resilience.
        </p>

        {stats && (
          <div style={{ marginTop: '20px' }}>
            <h3>System Stats</h3>
            <ul>
              <li>Total Listings: {stats.total_listings}</li>
              <li>Active Offers: {stats.active_offers}</li>
              <li>Active Needs: {stats.active_needs}</li>
            </ul>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Quick Actions</h2>
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
          <Link to="/create">
            <button>Create Offer</button>
          </Link>
          <Link to="/browse">
            <button className="secondary">Browse Offers</button>
          </Link>
        </div>
      </div>

      <div className="card">
        <h2>How It Works</h2>
        <ol>
          <li><strong>Create Offers</strong> - Share what you have available (food, tools, skills, etc.)</li>
          <li><strong>Browse Needs</strong> - See what others need in the community</li>
          <li><strong>Match and Exchange</strong> - Connect with others and coordinate handoffs</li>
          <li><strong>Record Events</strong> - Track resource flows for accountability</li>
        </ol>
      </div>
    </div>
  )
}

export default HomePage
