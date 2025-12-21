import React from 'react';

export function NetworkStatus() {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '0.5rem',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      padding: '1.5rem'
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{
            fontWeight: '600',
            fontSize: '1.125rem',
            color: '#111827',
            margin: 0
          }}>
            Network Status
          </h3>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <span style={{ fontSize: '1.25rem' }}>📡</span>
            <span style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.875rem',
              fontWeight: '500',
              backgroundColor: '#fef3c7',
              color: '#92400e'
            }}>
              Demo Mode
            </span>
          </div>
        </div>

        <div style={{
          backgroundColor: '#fffbeb',
          border: '1px solid #fbbf24',
          borderRadius: '0.5rem',
          padding: '1rem'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.5rem'
          }}>
            <span style={{ fontSize: '1rem' }}>🌐</span>
            <p style={{
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#92400e',
              margin: 0
            }}>
              Mesh Network
            </p>
          </div>
          <p style={{
            fontSize: '1.125rem',
            fontWeight: '700',
            color: '#b45309',
            margin: 0
          }}>
            Local Development Mode
          </p>
          <p style={{
            fontSize: '0.75rem',
            color: '#92400e',
            margin: '0.25rem 0 0 0'
          }}>
            Connect to physical mesh network for full functionality
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
          fontSize: '0.875rem'
        }}>
          <div>
            <p style={{ color: '#6b7280', margin: '0 0 0.25rem 0' }}>Node ID</p>
            <p style={{
              fontFamily: 'monospace',
              color: '#111827',
              margin: 0,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              dev-node-001...
            </p>
          </div>
          <div>
            <p style={{ color: '#6b7280', margin: '0 0 0.25rem 0' }}>Status</p>
            <p style={{
              color: '#059669',
              fontWeight: '500',
              margin: 0
            }}>
              Ready for Testing
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
