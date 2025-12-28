# Tasks: Agent Proposal Approval Notification System

## Phase 1: Basic Notification Infrastructure

### Task 1.1: Create notification badge component
- [ ] Create `frontend/src/components/NotificationBadge.tsx`
- [ ] Add bell icon from lucide-react
- [ ] Add count badge overlay
- [ ] Style badge (red background, white text)
- [ ] Add click handler to toggle dropdown
- [ ] Add ARIA labels for accessibility

### Task 1.2: Create notification dropdown component
- [ ] Create `frontend/src/components/NotificationDropdown.tsx`
- [ ] Add dropdown container with positioning
- [ ] Add header with "Notifications" title
- [ ] Add empty state message
- [ ] Add close button
- [ ] Handle click-outside to close

### Task 1.3: Create notification item component
- [ ] Create `frontend/src/components/NotificationItem.tsx`
- [ ] Display agent name
- [ ] Display proposal title
- [ ] Display timestamp (relative, e.g., "2 hours ago")
- [ ] Add priority indicator (color coding)
- [ ] Add click handler to view proposal
- [ ] Add hover state styling

### Task 1.4: Create useNotifications hook
- [ ] Create `frontend/src/hooks/useNotifications.ts`
- [ ] Fetch pending proposals on mount
- [ ] Track dropdown open/close state
- [ ] Calculate pending count
- [ ] Provide toggle function
- [ ] Handle loading and error states

### Task 1.5: Integrate badge into navigation
- [ ] Add NotificationBadge to Navigation component
- [ ] Position badge in header
- [ ] Connect to useNotifications hook
- [ ] Ensure responsive design
- [ ] Test mobile view

## Phase 2: Proposal Approval Interface

### Task 2.1: Create proposal approval modal
- [ ] Create `frontend/src/components/ProposalApprovalModal.tsx`
- [ ] Display full proposal details
- [ ] Add approve button
- [ ] Add reject button
- [ ] Add comment textarea
- [ ] Add close/cancel button

### Task 2.2: Implement approve action
- [ ] Call POST /api/agents/proposals/:id/approve
- [ ] Handle success response
- [ ] Show success toast
- [ ] Update proposals list (remove approved)
- [ ] Decrement badge count
- [ ] Handle error cases

### Task 2.3: Implement reject action
- [ ] Call POST /api/agents/proposals/:id/reject
- [ ] Require rejection reason (comment)
- [ ] Handle success response
- [ ] Show toast notification
- [ ] Update proposals list (remove rejected)
- [ ] Decrement badge count
- [ ] Handle error cases

### Task 2.4: Add comment functionality
- [ ] Call POST /api/agents/proposals/:id/comment
- [ ] Validate comment not empty
- [ ] Show comment in proposal history
- [ ] Handle success/error states

### Task 2.5: Test approval workflow
- [ ] Test approve flow end-to-end
- [ ] Test reject flow end-to-end
- [ ] Test validation (reject requires comment)
- [ ] Test error handling
- [ ] Verify badge count updates

## Phase 3: Real-time Updates

### Task 3.1: Set up WebSocket connection
- [ ] Create `frontend/src/hooks/useWebSocket.ts`
- [ ] Connect to NATS via WebSocket proxy (if available)
- [ ] Handle connection/disconnection
- [ ] Subscribe to agent proposal events
- [ ] Parse incoming messages
- [ ] Provide message hook to consumers

### Task 3.2: Subscribe to proposal events
- [ ] Subscribe to `{project}.agents.proposals.created`
- [ ] Subscribe to `{project}.agents.proposals.updated`
- [ ] Parse event payloads
- [ ] Update proposals list in real-time
- [ ] Handle reconnection logic

### Task 3.3: Implement live notifications
- [ ] Show toast when new proposal created
- [ ] Update badge count immediately
- [ ] Add new proposal to dropdown list
- [ ] Play notification sound (optional)
- [ ] Respect user preferences

### Task 3.4: Handle proposal updates
- [ ] Update proposal in list when status changes
- [ ] Remove from pending when approved/rejected
- [ ] Update badge count
- [ ] Close modal if currently viewing updated proposal

### Task 3.5: Test real-time updates
- [ ] Test new proposal notification
- [ ] Test badge count updates
- [ ] Test dropdown list updates
- [ ] Test with multiple proposals
- [ ] Test reconnection after disconnect

## Phase 4: Polish and Preferences

### Task 4.1: Add notification preferences UI
- [ ] Create settings page section for notifications
- [ ] Add toggle for toast notifications
- [ ] Add toggle for badge notifications
- [ ] Add priority filter (minimum priority)
- [ ] Save preferences to localStorage

### Task 4.2: Implement preference logic
- [ ] Check preferences before showing toast
- [ ] Check preferences before showing badge
- [ ] Filter proposals by minimum priority
- [ ] Respect user settings across sessions

### Task 4.3: Add priority styling
- [ ] Add red styling for emergency proposals
- [ ] Add orange styling for high-priority
- [ ] Add default styling for medium/low
- [ ] Sort proposals by priority in dropdown
- [ ] Add priority icons/badges

### Task 4.4: Improve accessibility
- [ ] Add keyboard navigation for dropdown
- [ ] Add Escape key to close dropdown
- [ ] Add focus management in modal
- [ ] Ensure proper ARIA attributes
- [ ] Test with screen reader

### Task 4.5: Add animations/transitions
- [ ] Animate badge count changes
- [ ] Animate dropdown open/close
- [ ] Animate new proposal additions
- [ ] Keep animations subtle and fast
- [ ] Respect prefers-reduced-motion

## Phase 5: Testing and Documentation

### Task 5.1: Write component tests
- [ ] Test NotificationBadge rendering
- [ ] Test NotificationDropdown interactions
- [ ] Test useNotifications hook
- [ ] Test ProposalApprovalModal actions
- [ ] Test WebSocket connection/reconnection

### Task 5.2: Write integration tests
- [ ] Test full approval workflow
- [ ] Test real-time updates
- [ ] Test preference settings
- [ ] Test error scenarios
- [ ] Test accessibility

### Task 5.3: Update documentation
- [ ] Document notification system in README
- [ ] Add component documentation
- [ ] Document WebSocket event format
- [ ] Add troubleshooting guide
- [ ] Document user preferences

### Task 5.4: Create user guide
- [ ] Explain how notifications work
- [ ] Document how to approve proposals
- [ ] Explain priority levels
- [ ] Document preference settings
- [ ] Add screenshots/GIFs

## Acceptance Checklist

- [ ] Notification badge shows correct count
- [ ] Clicking badge opens dropdown with proposals
- [ ] Users can approve/reject proposals
- [ ] Real-time updates work without refresh
- [ ] Toast notifications appear for new proposals
- [ ] Preferences are saved and respected
- [ ] Priority styling is clear and consistent
- [ ] Accessibility requirements met
- [ ] All tests pass
- [ ] Documentation complete

## Estimated Timeline

- Phase 1: 8 hours
- Phase 2: 6 hours
- Phase 3: 6 hours
- Phase 4: 6 hours
- Phase 5: 4 hours
- **Total: ~30 hours** (revised from initial 23h estimate)

## Dependencies

- Backend API endpoints (verify they exist)
- NATS event streaming setup
- WebSocket proxy (or alternative real-time solution)
- Toast notification system (sonner - already installed)

## Notes

- WebSocket integration may require backend work if not already available
- Consider polling as fallback if WebSocket unavailable
- Priority should be: basic notifications → approval interface → real-time updates → polish
- Can ship Phase 1-2 as MVP, then add Phase 3-4 in follow-up
