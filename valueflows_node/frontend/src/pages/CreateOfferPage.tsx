import React from 'react'
import { useNavigate } from 'react-router-dom'
import CreateOfferForm from '../components/CreateOfferForm'

function CreateOfferPage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    navigate('/browse')
  }

  return (
    <div className="card">
      <h2>Create Offer</h2>
      <p>Share what you have available with the community</p>
      <div style={{ marginTop: '20px' }}>
        <CreateOfferForm onSuccess={handleSuccess} />
      </div>
    </div>
  )
}

export default CreateOfferPage
