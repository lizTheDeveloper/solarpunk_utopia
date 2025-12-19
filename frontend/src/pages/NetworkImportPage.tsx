/**
 * Network Import Page - Steward Bulk Vouching
 *
 * Enables stewards to import existing communities WITHOUT external platforms:
 * - Bulk vouch for people they know personally
 * - Create threshold-signed attestations
 * - View accountability metrics
 *
 * Works fully offline (no internet required).
 */
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Alert,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Add as AddIcon,
  Upload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

interface VoucheeInput {
  name: string;
  identifier: string; // Could be email or user ID
}

export default function NetworkImportPage() {
  const navigate = useNavigate();
  const [vouchees, setVouchees] = useState<VoucheeInput[]>([
    { name: '', identifier: '' }
  ]);
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [accountability, setAccountability] = useState<any>(null);

  // Load steward accountability on mount
  React.useEffect(() => {
    loadAccountability();
  }, []);

  const loadAccountability = async () => {
    try {
      const response = await api.get('/attestation/steward/my-accountability');
      setAccountability(response.data);
    } catch (err: any) {
      // Not a steward yet, that's OK
      console.log('Not a steward or no accountability record yet');
    }
  };

  const addVouchee = () => {
    setVouchees([...vouchees, { name: '', identifier: '' }]);
  };

  const removeVouchee = (index: number) => {
    setVouchees(vouchees.filter((_, i) => i !== index));
  };

  const updateVouchee = (index: number, field: 'name' | 'identifier', value: string) => {
    const updated = [...vouchees];
    updated[index][field] = value;
    setVouchees(updated);
  };

  const handleBulkVouch = async () => {
    setError(null);
    setSuccess(null);

    // Validation
    if (!context.trim()) {
      setError('Please specify how you know these people');
      return;
    }

    const validVouchees = vouchees.filter(v => v.name.trim() && v.identifier.trim());
    if (validVouchees.length === 0) {
      setError('Please add at least one person to vouch for');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/attestation/bulk-vouch', {
        vouchees: validVouchees,
        context: context,
        attestation: 'met_in_person',
      });

      const { vouches_created, failed_identifiers, message } = response.data;

      setSuccess(
        `Successfully vouched for ${vouches_created} people! ${
          failed_identifiers.length > 0
            ? `(${failed_identifiers.length} already vouched or failed)`
            : ''
        }`
      );

      // Reset form
      setVouchees([{ name: '', identifier: '' }]);
      setContext('');

      // Reload accountability
      loadAccountability();

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to bulk vouch. Are you a steward?');
    } finally {
      setLoading(false);
    }
  };

  const handleCSVImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter(line => line.trim());

      // Skip header if present
      const startIndex = lines[0].toLowerCase().includes('name') ? 1 : 0;

      const imported = lines.slice(startIndex).map(line => {
        const [name, identifier] = line.split(',').map(s => s.trim());
        return { name, identifier };
      }).filter(v => v.name && v.identifier);

      setVouchees(imported);
      setSuccess(`Imported ${imported.length} people from CSV`);
    };

    reader.readAsText(file);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'warning':
        return 'warning';
      case 'suspended':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        Network Import
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        As a steward, you can vouch for people you know personally to import existing communities.
        This works WITHOUT external platforms - fully offline and privacy-preserving.
      </Typography>

      {/* Accountability Card */}
      {accountability && (
        <Card sx={{ mb: 3, bgcolor: accountability.status === 'active' ? 'background.paper' : 'warning.light' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Your Vouching Record
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Total Vouches
                </Typography>
                <Typography variant="h5">
                  {accountability.total_vouches}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Revocation Rate
                </Typography>
                <Typography variant="h5" color={accountability.revocation_rate > 0.1 ? 'error' : 'success'}>
                  {(accountability.revocation_rate * 100).toFixed(1)}%
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Chip
                  label={accountability.status.toUpperCase()}
                  color={getStatusColor(accountability.status)}
                  icon={accountability.status === 'active' ? <CheckCircleIcon /> : <WarningIcon />}
                />
              </Grid>
            </Grid>
            {accountability.status !== 'active' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Your vouching privileges are {accountability.status}.
                {accountability.revocation_rate > 0.2
                  ? ' Too many of your vouches were revoked (infiltrators). Please be more careful.'
                  : ' Some of your vouches were revoked. Review your vouching process.'}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            People to Vouch For
          </Typography>
          <Box>
            <input
              accept=".csv"
              style={{ display: 'none' }}
              id="csv-upload"
              type="file"
              onChange={handleCSVImport}
            />
            <label htmlFor="csv-upload">
              <Button
                component="span"
                startIcon={<UploadIcon />}
                variant="outlined"
                size="small"
                sx={{ mr: 1 }}
              >
                Import CSV
              </Button>
            </label>
            <Button
              startIcon={<AddIcon />}
              onClick={addVouchee}
              variant="outlined"
              size="small"
            >
              Add Person
            </Button>
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary" paragraph>
          CSV format: name,identifier (e.g., "Alex K.,alex@example.com")
        </Typography>

        <List>
          {vouchees.map((vouchee, index) => (
            <ListItem
              key={index}
              sx={{
                display: 'flex',
                gap: 2,
                alignItems: 'center',
                mb: 1,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                p: 2,
              }}
            >
              <TextField
                label="Name"
                value={vouchee.name}
                onChange={(e) => updateVouchee(index, 'name', e.target.value)}
                size="small"
                fullWidth
                placeholder="e.g., Alex K."
              />
              <TextField
                label="Identifier"
                value={vouchee.identifier}
                onChange={(e) => updateVouchee(index, 'identifier', e.target.value)}
                size="small"
                fullWidth
                placeholder="e.g., alex@example.com or user-pk-123"
              />
              <IconButton
                onClick={() => removeVouchee(index)}
                disabled={vouchees.length === 1}
                color="error"
              >
                <DeleteIcon />
              </IconButton>
            </ListItem>
          ))}
        </List>

        <TextField
          label="How do you know these people?"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          fullWidth
          multiline
          rows={2}
          placeholder="e.g., 'food_co_op_members', 'bootcamp_cohort_2019', 'workshop_attendees'"
          sx={{ mt: 2 }}
          helperText="Describe your relationship - helps track vouch quality"
        />

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleBulkVouch}
            disabled={loading || accountability?.status === 'suspended'}
            fullWidth
          >
            {loading ? 'Vouching...' : `Vouch for ${vouchees.filter(v => v.name && v.identifier).length} People`}
          </Button>
          <Button
            variant="outlined"
            onClick={() => navigate('/network')}
          >
            Cancel
          </Button>
        </Box>
      </Paper>

      {/* Info Section */}
      <Paper sx={{ p: 3, bgcolor: 'info.light' }}>
        <Typography variant="h6" gutterBottom>
          How Network Import Works
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>NO External Platforms:</strong> This works completely offline. No OAuth, no APIs, no dependencies on corporations.
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Steward Accountability:</strong> Your vouches are tracked. If too many turn out to be infiltrators,
          your vouching privileges will be suspended. Be careful who you vouch for!
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Trust Propagation:</strong> People you vouch for receive trust based on your trust level (×0.8 per hop).
          They can then participate in the network and vouch for others.
        </Typography>
        <Typography variant="body2">
          <strong>Privacy:</strong> Identifiers (email/phone) are only used to deliver invitations.
          Once people join, the network uses public keys. No personal data is stored centrally.
        </Typography>
      </Paper>
    </Container>
  );
}
