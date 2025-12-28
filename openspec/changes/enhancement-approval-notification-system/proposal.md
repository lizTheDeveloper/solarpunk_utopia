# Agent Proposal Approval Notification System

**Status:** Draft
**Priority:** High
**Component:** Frontend, Agent System
**Source:** USER_TESTING_REVIEW_2025-12-22.md Section 10.3, Opportunity 5

## Problem Statement

Agent proposals currently have no notification mechanism for pending approvals. Users are not alerted when agent proposals require their review, leading to delayed decision-making and stalled workflows.

**Impact:**
- Agent proposals sit unreviewed for extended periods
- Users must manually check for pending approvals
- Workflow bottlenecks in agent-driven automation
- Poor user experience for collaborative governance features
- Defeats the purpose of autonomous agent assistance

**Evidence from Review:**
```
Enhancement Opportunity 5: Notification System
- Agent proposals need approval notifications
- Currently no alert mechanism for pending approvals
- Would improve user experience significantly

Agent System: 🟡 Beta Quality
- ⚠️ Approval UI not implemented
```

## Requirements

### Notification Display (MUST implement)

1. **Notification Badge**
   - WHEN there are pending agent proposals
   - THEN a badge SHALL appear on the navigation menu
   - AND the badge MUST show the count of pending proposals
   - AND the badge SHALL be visually prominent (red color)

2. **Notification List**
   - WHEN a user clicks on notifications
   - THEN they SHALL see a list of pending proposals
   - AND each notification MUST show:
     - Agent name
     - Proposal title
     - Proposal timestamp
     - Priority/urgency indicator
   - AND notifications MUST be sortable by date and priority

3. **Proposal Review Interface**
   - WHEN a user clicks on a notification
   - THEN they SHALL be taken to the proposal details page
   - AND they MUST be able to approve or reject the proposal
   - AND they MUST be able to add comments
   - AND the action MUST be recorded with timestamp

### Real-time Updates (SHOULD implement)

1. **Live Notifications**
   - WHEN a new agent proposal is created
   - THEN the user SHALL see a toast notification
   - AND the notification badge count SHALL update immediately
   - WITHOUT requiring page refresh

2. **WebSocket Integration**
   - Connect to NATS event stream for proposal events
   - Subscribe to `{project}.agents.proposals.>`
   - Update UI in real-time when proposals are created/updated

### Notification Preferences (SHOULD implement)

1. **User Settings**
   - Users SHALL be able to configure notification preferences
   - Options:
     - Enable/disable toast notifications
     - Enable/disable badge notifications
     - Set minimum priority for notifications
     - Email notifications (future)

### Agent-Specific Rules (SHOULD implement)

1. **Priority Routing**
   - Emergency agent proposals MUST show urgent styling
   - Critical proposals SHOULD appear at top of list
   - Low-priority proposals MAY be collapsed by default

2. **Auto-Approval Thresholds**
   - Users SHALL be able to set auto-approval for trusted agents
   - Users SHALL be able to set approval thresholds by agent type
   - Critical proposals MUST never auto-approve

## Success Criteria

- [ ] Notification badge appears on navigation with accurate count
- [ ] Toast notifications appear when new proposals are created
- [ ] Users can view all pending proposals in one place
- [ ] Users can approve/reject proposals from notification interface
- [ ] Notification count updates in real-time
- [ ] System is accessible (ARIA labels, keyboard navigation)

## Non-Goals

- Email notifications (future enhancement)
- Mobile push notifications (future enhancement)
- Notification history/archive (future enhancement)
- Batch approval operations (future enhancement)

## Dependencies

- Agent proposal API endpoints (already exist)
- NATS event streaming for real-time updates
- WebSocket client for frontend
- Toast notification system (already implemented with sonner)

## Technical Design

### Frontend Components

**Components to Create:**
```
frontend/src/components/NotificationBadge.tsx
frontend/src/components/NotificationDropdown.tsx
frontend/src/components/NotificationItem.tsx
frontend/src/components/ProposalApprovalModal.tsx
frontend/src/hooks/useNotifications.ts
frontend/src/hooks/useWebSocket.ts
```

**Navigation Integration:**
```typescript
// In Navigation component
<NotificationBadge count={pendingProposals.length} onClick={openDropdown} />

// Dropdown shows:
<NotificationDropdown proposals={pendingProposals}>
  {proposals.map(p => (
    <NotificationItem
      key={p.id}
      agent={p.agent_name}
      title={p.title}
      priority={p.priority}
      timestamp={p.created_at}
      onClick={() => openProposal(p.id)}
    />
  ))}
</NotificationDropdown>
```

### Backend API Endpoints

**Existing:**
- `GET /api/agents/proposals` - List all proposals
- `GET /api/agents/proposals/:id` - Get proposal details
- `POST /api/agents/proposals/:id/approve` - Approve proposal
- `POST /api/agents/proposals/:id/reject` - Reject proposal

**New (if needed):**
- `GET /api/agents/proposals/pending` - Filter for pending only
- `PATCH /api/agents/proposals/:id/status` - Update status
- `POST /api/agents/proposals/:id/comment` - Add comment

### NATS Event Integration

**Subscribe to:**
```
{project}.agents.proposals.created
{project}.agents.proposals.updated
{project}.agents.proposals.approved
{project}.agents.proposals.rejected
```

**Event Payload:**
```typescript
interface ProposalEvent {
  proposal_id: string;
  agent_name: string;
  title: string;
  priority: 'low' | 'medium' | 'high' | 'critical' | 'emergency';
  status: 'pending' | 'approved' | 'rejected';
  timestamp: string;
}
```

## Acceptance Tests

### Scenario 1: New Proposal Notification
```
GIVEN a user is logged in and viewing the app
WHEN an agent creates a new proposal
THEN a toast notification SHALL appear
AND the notification badge count SHALL increase by 1
AND the badge SHALL be visible in the navigation
```

### Scenario 2: Viewing Pending Proposals
```
GIVEN there are 3 pending agent proposals
WHEN the user clicks the notification badge
THEN they SHALL see a dropdown with 3 proposals
AND each proposal SHALL show agent name, title, and timestamp
AND the proposals SHALL be sorted by priority (highest first)
```

### Scenario 3: Approving a Proposal
```
GIVEN the user views a proposal notification
WHEN they click on the notification
THEN they SHALL see the proposal details modal
AND they SHALL see "Approve" and "Reject" buttons
WHEN they click "Approve"
THEN the proposal status SHALL change to "approved"
AND the notification SHALL be removed from the list
AND the badge count SHALL decrease by 1
AND a success toast SHALL appear
```

### Scenario 4: Real-time Update
```
GIVEN the user has the notification dropdown open
WHEN a new proposal is created (by another agent)
THEN the dropdown SHALL update to show the new proposal
AND the badge count SHALL increment
WITHOUT the user refreshing the page
```

### Scenario 5: Priority Indication
```
GIVEN there are proposals with different priorities
WHEN the user views the notification list
THEN emergency proposals SHALL have red styling
AND high-priority proposals SHALL have orange styling
AND medium/low proposals SHALL have default styling
AND proposals SHALL be sorted by priority
```

## Implementation Notes

### Phase 1: Basic Notifications (Essential)
1. Create notification badge component
2. Add badge to navigation
3. Fetch pending proposals on page load
4. Display count in badge
5. Create dropdown with proposal list
6. Add click handlers to navigate to proposals

### Phase 2: Approval Interface (Essential)
1. Create proposal approval modal
2. Add approve/reject buttons
3. Integrate with existing API endpoints
4. Update badge count after actions
5. Show success/error toasts

### Phase 3: Real-time Updates (Important)
1. Set up WebSocket connection to NATS
2. Subscribe to proposal events
3. Update badge count on new proposals
4. Update dropdown list in real-time
5. Show toast on new proposals

### Phase 4: Polish (Nice-to-have)
1. Add notification preferences
2. Add auto-approval rules
3. Add accessibility features
4. Add animations/transitions

## Example Code

### NotificationBadge Component
```typescript
// frontend/src/components/NotificationBadge.tsx
import { Bell } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';

export function NotificationBadge() {
  const { pendingCount, isOpen, toggle } = useNotifications();

  return (
    <button
      onClick={toggle}
      className="relative p-2 hover:bg-gray-100 rounded-full"
      aria-label={`${pendingCount} pending notifications`}
    >
      <Bell className="w-6 h-6 text-gray-600" />
      {pendingCount > 0 && (
        <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
          {pendingCount > 9 ? '9+' : pendingCount}
        </span>
      )}
    </button>
  );
}
```

### useNotifications Hook
```typescript
// frontend/src/hooks/useNotifications.ts
import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { toast } from 'sonner';

export function useNotifications() {
  const [proposals, setProposals] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  // Fetch initial proposals
  useEffect(() => {
    fetch('/api/agents/proposals/pending')
      .then(res => res.json())
      .then(data => setProposals(data));
  }, []);

  // Subscribe to real-time updates
  const { message } = useWebSocket('agents.proposals.>');
  useEffect(() => {
    if (message?.event === 'created') {
      setProposals(prev => [message.proposal, ...prev]);
      toast.info(`New proposal from ${message.proposal.agent_name}`);
    }
  }, [message]);

  return {
    proposals,
    pendingCount: proposals.length,
    isOpen,
    toggle: () => setIsOpen(!isOpen),
  };
}
```

## Estimated Effort

- Basic notification badge: 3 hours
- Notification dropdown: 4 hours
- Approval modal: 4 hours
- API integration: 2 hours
- WebSocket/NATS integration: 6 hours
- Testing and polish: 4 hours

**Total: ~23 hours**

## Related Issues

- Agent System currently at "Beta Quality" per section 12.1
- Approval UI not implemented (section 12.1)
- Would significantly improve user experience (section 10.3)
- Enables full agent workflow automation
