/**
 * Attestation Claim Page
 *
 * Allows users to claim attestations (cohort membership, organization affiliation, etc.)
 * via three verification methods:
 * 1. In-person verification by steward
 * 2. Challenge-response (answer question only real members know)
 * 3. Mesh vouch (existing verified member vouches)
 *
 * Works fully offline (no internet required).
 */
import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Alert,
  Card,
  CardContent,
  CardActions,
  Chip,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  VerifiedUser as VerifiedIcon,
  QuestionAnswer as QuestionIcon,
  Group as GroupIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

interface Attestation {
  id: string;
  type: string;
  subject_identifier: string;
  claims: Record<string, string>;
  created_at: string;
  expires_at?: string;
}

interface ChallengeQuestion {
  id: string;
  question: string;
  attestation_id: string;
}

export default function AttestationClaimPage() {
  const navigate = useNavigate();
  const [attestations, setAttestations] = useState<Attestation[]>([]);
  const [selectedAttestation, setSelectedAttestation] = useState<Attestation | null>(null);
  const [verificationMethod, setVerificationMethod] = useState<'in_person' | 'challenge' | 'mesh_vouch'>('in_person');
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // In-person verification
  const [stewardId, setStewardId] = useState('');

  // Challenge verification
  const [challenges, setChallenges] = useState<ChallengeQuestion[]>([]);
  const [selectedChallenge, setSelectedChallenge] = useState<ChallengeQuestion | null>(null);
  const [challengeAnswer, setChallengeAnswer] = useState('');

  // Mesh vouch verification
  const [voucherId, setVoucherId] = useState('');

  // My claims
  const [myClaims, setMyClaims] = useState<any[]>([]);

  useEffect(() => {
    loadAttestations();
    loadMyClaims();
  }, []);

  const loadAttestations = async () => {
    try {
      // Load cohort attestations (most common)
      const response = await api.get('/attestation/type/cohort');
      setAttestations(response.data);
    } catch (err) {
      console.error('Failed to load attestations:', err);
    }
  };

  const loadMyClaims = async () => {
    try {
      const response = await api.get('/attestation/claims/my');
      setMyClaims(response.data);
    } catch (err) {
      console.error('Failed to load my claims:', err);
    }
  };

  const loadChallenges = async (attestationId: string) => {
    try {
      const response = await api.get(`/attestation/challenge/${attestationId}`);
      setChallenges(response.data);
      if (response.data.length > 0) {
        setSelectedChallenge(response.data[0]);
      }
    } catch (err) {
      console.error('Failed to load challenges:', err);
    }
  };

  const handleSelectAttestation = (attestation: Attestation) => {
    setSelectedAttestation(attestation);
    setActiveStep(1);
    setError(null);
    setSuccess(null);

    // Load challenges if needed
    if (verificationMethod === 'challenge') {
      loadChallenges(attestation.id);
    }
  };

  const handleClaimInPerson = async () => {
    if (!selectedAttestation || !stewardId.trim()) {
      setError('Please enter the steward ID who verified you in person');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/attestation/claim/in-person', null, {
        params: {
          attestation_id: selectedAttestation.id,
          verifier_steward_id: stewardId,
        },
      });

      setSuccess(response.data.message);
      setActiveStep(3);
      loadMyClaims();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to claim attestation');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimChallenge = async () => {
    if (!selectedAttestation || !selectedChallenge || !challengeAnswer.trim()) {
      setError('Please answer the challenge question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/attestation/claim/challenge', null, {
        params: {
          attestation_id: selectedAttestation.id,
          challenge_id: selectedChallenge.id,
          answer: challengeAnswer,
        },
      });

      setSuccess(response.data.message);
      setActiveStep(3);
      loadMyClaims();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Incorrect answer or failed to claim');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimMeshVouch = async () => {
    if (!selectedAttestation || !voucherId.trim()) {
      setError('Please enter the ID of a verified cohort member who can vouch for you');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/attestation/claim/mesh-vouch', null, {
        params: {
          attestation_id: selectedAttestation.id,
          voucher_cohort_member_id: voucherId,
        },
      });

      setSuccess(response.data.message);
      setActiveStep(3);
      loadMyClaims();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to claim via mesh vouch');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitClaim = () => {
    switch (verificationMethod) {
      case 'in_person':
        handleClaimInPerson();
        break;
      case 'challenge':
        handleClaimChallenge();
        break;
      case 'mesh_vouch':
        handleClaimMeshVouch();
        break;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'success';
      case 'pending':
        return 'warning';
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTrustBonusDisplay = (trustGranted: number) => {
    return `+${(trustGranted * 100).toFixed(0)}%`;
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        Claim Attestation
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Claim membership in cohorts, organizations, or groups you belong to.
        All verification happens offline - no external platforms required.
      </Typography>

      {/* My Claims */}
      {myClaims.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            My Verified Attestations
          </Typography>
          <List>
            {myClaims.filter(c => c.status === 'verified').map((claim) => (
              <ListItem key={claim.id} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                <CheckCircleIcon color="success" sx={{ mr: 2 }} />
                <ListItemText
                  primary={`Attestation ${claim.attestation_id}`}
                  secondary={`Verified via ${claim.verification_method} • Trust bonus: ${getTrustBonusDisplay(claim.trust_granted)}`}
                />
                <Chip label={claim.status} color={getStatusColor(claim.status)} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        <Step>
          <StepLabel>Select Attestation</StepLabel>
        </Step>
        <Step>
          <StepLabel>Choose Verification Method</StepLabel>
        </Step>
        <Step>
          <StepLabel>Complete Verification</StepLabel>
        </Step>
      </Stepper>

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

      {/* Step 1: Select Attestation */}
      {activeStep === 0 && (
        <Grid container spacing={2}>
          {attestations.map((attestation) => (
            <Grid item xs={12} md={6} key={attestation.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {attestation.subject_identifier}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Type: {attestation.type}
                  </Typography>
                  {Object.entries(attestation.claims).map(([key, value]) => (
                    <Chip key={key} label={`${key}: ${value}`} size="small" sx={{ mr: 1, mb: 1 }} />
                  ))}
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={() => handleSelectAttestation(attestation)}
                  >
                    Claim This
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Step 1: Choose Verification Method */}
      {activeStep === 1 && selectedAttestation && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            How would you like to verify?
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: verificationMethod === 'in_person' ? 2 : 1,
                  borderColor: verificationMethod === 'in_person' ? 'primary.main' : 'divider',
                }}
                onClick={() => setVerificationMethod('in_person')}
              >
                <CardContent>
                  <VerifiedIcon fontSize="large" color="primary" />
                  <Typography variant="h6" gutterBottom>
                    In-Person
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Steward confirms your identity face-to-face. Gold standard verification. Grants highest trust bonus.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: verificationMethod === 'challenge' ? 2 : 1,
                  borderColor: verificationMethod === 'challenge' ? 'primary.main' : 'divider',
                }}
                onClick={() => {
                  setVerificationMethod('challenge');
                  loadChallenges(selectedAttestation.id);
                }}
              >
                <CardContent>
                  <QuestionIcon fontSize="large" color="primary" />
                  <Typography variant="h6" gutterBottom>
                    Challenge
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Answer a question only real members know. Works offline. Grants moderate trust bonus.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: verificationMethod === 'mesh_vouch' ? 2 : 1,
                  borderColor: verificationMethod === 'mesh_vouch' ? 'primary.main' : 'divider',
                }}
                onClick={() => setVerificationMethod('mesh_vouch')}
              >
                <CardContent>
                  <GroupIcon fontSize="large" color="primary" />
                  <Typography variant="h6" gutterBottom>
                    Mesh Vouch
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Existing verified member vouches for you. Works via mesh. Grants basic trust bonus.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Button variant="contained" onClick={() => setActiveStep(2)}>
            Continue
          </Button>
        </Paper>
      )}

      {/* Step 2: Complete Verification */}
      {activeStep === 2 && selectedAttestation && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Complete {verificationMethod.replace('_', ' ')} Verification
          </Typography>

          {verificationMethod === 'in_person' && (
            <Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Have a steward confirm your identity in person. They will provide their steward ID.
              </Typography>
              <TextField
                label="Steward ID"
                value={stewardId}
                onChange={(e) => setStewardId(e.target.value)}
                fullWidth
                placeholder="steward-pk-123"
                helperText="Ask the steward for their ID"
              />
            </Box>
          )}

          {verificationMethod === 'challenge' && (
            <Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Answer a question that only real members of this cohort would know.
              </Typography>
              {challenges.length > 0 ? (
                <>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Select Challenge</InputLabel>
                    <Select
                      value={selectedChallenge?.id || ''}
                      onChange={(e) => {
                        const challenge = challenges.find(c => c.id === e.target.value);
                        setSelectedChallenge(challenge || null);
                      }}
                    >
                      {challenges.map((challenge) => (
                        <MenuItem key={challenge.id} value={challenge.id}>
                          {challenge.question}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    label="Your Answer"
                    value={challengeAnswer}
                    onChange={(e) => setChallengeAnswer(e.target.value)}
                    fullWidth
                    placeholder="Type your answer here"
                  />
                </>
              ) : (
                <Alert severity="info">
                  No challenge questions available for this attestation. Try in-person or mesh vouch verification.
                </Alert>
              )}
            </Box>
          )}

          {verificationMethod === 'mesh_vouch' && (
            <Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Ask an existing verified member of this cohort to vouch for you.
              </Typography>
              <TextField
                label="Verified Member ID"
                value={voucherId}
                onChange={(e) => setVoucherId(e.target.value)}
                fullWidth
                placeholder="user-pk-456"
                helperText="Ask them for their user ID"
              />
            </Box>
          )}

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleSubmitClaim}
              disabled={loading}
            >
              {loading ? 'Verifying...' : 'Submit Claim'}
            </Button>
            <Button variant="outlined" onClick={() => setActiveStep(1)}>
              Back
            </Button>
          </Box>
        </Paper>
      )}
    </Container>
  );
}
