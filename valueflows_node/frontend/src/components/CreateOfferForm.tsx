import React, { useState } from 'react'

const CATEGORIES = [
  { value: 'food', label: 'Food' },
  { value: 'tools', label: 'Tools' },
  { value: 'seeds', label: 'Seeds' },
  { value: 'skills', label: 'Skills' },
  { value: 'labor', label: 'Labor' },
  { value: 'knowledge', label: 'Knowledge' },
  { value: 'housing', label: 'Housing' },
  { value: 'transportation', label: 'Transportation' },
  { value: 'materials', label: 'Materials' },
  { value: 'other', label: 'Other' },
]

interface CreateOfferFormProps {
  onSuccess?: () => void
}

function CreateOfferForm({ onSuccess }: CreateOfferFormProps) {
  const [formData, setFormData] = useState({
    listing_type: 'offer',
    title: '',
    description: '',
    category: 'food',
    quantity: 1,
    unit: 'items',
    agent_id: 'user:default', // In production, get from auth
    resource_spec_id: '', // Will be created/found automatically
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      // Create or find resource spec first
      const specResponse = await fetch('/vf/resource-specs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.title,
          category: formData.category,
        }),
      })

      const spec = await specResponse.json()
      const resourceSpecId = spec.id || `spec:${formData.category}:${Date.now()}`

      // Create listing
      const listingData = {
        ...formData,
        resource_spec_id: resourceSpecId,
        status: 'active',
      }

      const response = await fetch('/vf/listings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(listingData),
      })

      if (!response.ok) {
        throw new Error('Failed to create listing')
      }

      setSuccess(true)
      setFormData({
        listing_type: 'offer',
        title: '',
        description: '',
        category: 'food',
        quantity: 1,
        unit: 'items',
        agent_id: 'user:default',
        resource_spec_id: '',
      })

      if (onSuccess) {
        setTimeout(onSuccess, 1500)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create offer')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">Offer created successfully!</div>}

      <div className="form-group">
        <label>Type</label>
        <select name="listing_type" value={formData.listing_type} onChange={handleChange}>
          <option value="offer">Offer</option>
          <option value="need">Need</option>
        </select>
      </div>

      <div className="form-group">
        <label>Category *</label>
        <select name="category" value={formData.category} onChange={handleChange} required>
          {CATEGORIES.map(cat => (
            <option key={cat.value} value={cat.value}>{cat.label}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Title *</label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="e.g., Fresh tomatoes from garden"
          required
        />
      </div>

      <div className="form-group">
        <label>Description</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Add details about your offer..."
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div className="form-group">
          <label>Quantity *</label>
          <input
            type="number"
            name="quantity"
            value={formData.quantity}
            onChange={handleChange}
            min="0"
            step="0.1"
            required
          />
        </div>

        <div className="form-group">
          <label>Unit *</label>
          <input
            type="text"
            name="unit"
            value={formData.unit}
            onChange={handleChange}
            placeholder="lbs, hours, items"
            required
          />
        </div>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create Offer'}
      </button>
    </form>
  )
}

export default CreateOfferForm
