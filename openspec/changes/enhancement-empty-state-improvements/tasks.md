# Tasks: Frontend Empty State Improvements

## Phase 1: Create EmptyState Component

### Task 1.1: Design EmptyState component
- [ ] Create `frontend/src/components/EmptyState.tsx`
- [ ] Define TypeScript interface for props
- [ ] Accept icon, title, description, actions
- [ ] Implement consistent layout structure
- [ ] Add responsive design
- [ ] Export component

### Task 1.2: Style EmptyState component
- [ ] Add icon container with background
- [ ] Style heading (text-xl, semibold)
- [ ] Style description (text-gray-600)
- [ ] Add proper spacing (py-12, mb-4, etc.)
- [ ] Center content horizontally
- [ ] Ensure max-width for readability

### Task 1.3: Add action button support
- [ ] Support primary action button
- [ ] Support secondary action button
- [ ] Use existing Button component
- [ ] Center buttons with flex layout
- [ ] Add proper gap between buttons

### Task 1.4: Add accessibility features
- [ ] Mark icon as aria-hidden
- [ ] Use semantic HTML (h2/h3 for titles)
- [ ] Ensure keyboard navigation works
- [ ] Add proper color contrast
- [ ] Test with screen reader

### Task 1.5: Write component tests
- [ ] Test rendering with required props
- [ ] Test with optional action buttons
- [ ] Test with custom className
- [ ] Test accessibility attributes
- [ ] Add snapshot tests

## Phase 2: Migrate High-Impact Pages

### Task 2.1: Update HomePage
- [ ] Import EmptyState component
- [ ] Update offers section empty state
- [ ] Update needs section empty state
- [ ] Add icons (Package, Heart)
- [ ] Add CTAs to create offer/need
- [ ] Test visually

### Task 2.2: Update MessageThreadPage
- [ ] Import EmptyState component
- [ ] Replace text-only empty state
- [ ] Add MessageCircle icon
- [ ] Update messaging to be encouraging
- [ ] Remove old empty state code
- [ ] Test visually

### Task 2.3: Update ExchangesPage
- [ ] Import EmptyState component
- [ ] Replace basic text empty state
- [ ] Add ArrowRightLeft icon
- [ ] Add contextual messaging (filtered vs. empty)
- [ ] Add "Clear Filters" or "Create Offer" CTA
- [ ] Test both contexts (filtered and empty)

### Task 2.4: Update MessagesPage
- [ ] Import EmptyState component
- [ ] Update empty state for no messages
- [ ] Add contextual messaging (search vs. empty)
- [ ] Add icon if missing
- [ ] Improve description text
- [ ] Test visually

### Task 2.5: Update CellDetailPage
- [ ] Import EmptyState component
- [ ] Update "no members" empty state
- [ ] Update "no stewards" empty state
- [ ] Add Users icon
- [ ] Add appropriate CTAs (Join Cell, etc.)
- [ ] Test visually

## Phase 3: Migrate Remaining Pages

### Task 3.1: Update RapidResponsePage
- [ ] Import EmptyState component
- [ ] Update "no responders" empty state
- [ ] Update "no timeline updates" empty state
- [ ] Add appropriate icons
- [ ] Improve messaging
- [ ] Test visually

### Task 3.2: Update AgentsPage
- [ ] Import EmptyState component
- [ ] Update "no proposals" empty state
- [ ] Enhance description (already has icon)
- [ ] Make more actionable if possible
- [ ] Test visually

### Task 3.3: Update KnowledgePage
- [ ] Import EmptyState component
- [ ] Update "no files" empty state
- [ ] Add contextual messaging (category filter)
- [ ] Add appropriate icon (FileText, Upload)
- [ ] Add CTA to upload files
- [ ] Test visually

### Task 3.4: Update DiscoveryPage
- [ ] Import EmptyState component
- [ ] Update "no results" empty state
- [ ] Add Search or Globe icon
- [ ] Improve messaging for empty searches
- [ ] Test visually

### Task 3.5: Audit remaining pages
- [ ] Search codebase for other empty states
- [ ] Identify any missed empty states
- [ ] Update as needed
- [ ] Document any edge cases

## Phase 4: Documentation and Guidelines

### Task 4.1: Document EmptyState component
- [ ] Add JSDoc comments to component
- [ ] Create usage examples
- [ ] Document props and types
- [ ] Add to component library docs
- [ ] Include screenshots

### Task 4.2: Create design guidelines
- [ ] Document when to use EmptyState
- [ ] Provide messaging best practices
- [ ] List available icons for common cases
- [ ] Show good/bad examples
- [ ] Add to CONTRIBUTING.md

### Task 4.3: Create component Storybook stories
- [ ] Add EmptyState to Storybook (if available)
- [ ] Create stories for different variants
- [ ] Show with/without actions
- [ ] Show different icons
- [ ] Make interactive

### Task 4.4: Update design system docs
- [ ] Add EmptyState to design system
- [ ] Document standard patterns
- [ ] List common use cases
- [ ] Provide copy guidelines
- [ ] Include accessibility notes

## Phase 5: Testing and Validation

### Task 5.1: Visual regression testing
- [ ] Take screenshots of all updated pages
- [ ] Compare before/after
- [ ] Verify consistency across pages
- [ ] Check responsive design
- [ ] Document any issues

### Task 5.2: Accessibility testing
- [ ] Test with screen reader (VoiceOver/NVDA)
- [ ] Verify keyboard navigation
- [ ] Check color contrast ratios
- [ ] Validate semantic HTML
- [ ] Fix any issues found

### Task 5.3: User testing (if possible)
- [ ] Get feedback on new empty states
- [ ] Verify messaging is clear
- [ ] Check if CTAs are obvious
- [ ] Iterate based on feedback

### Task 5.4: Update tests
- [ ] Update page component tests
- [ ] Add tests for EmptyState component
- [ ] Verify no regressions
- [ ] Update snapshots if needed

## Acceptance Checklist

- [ ] EmptyState component created and documented
- [ ] All high-impact pages migrated (5 pages)
- [ ] All remaining pages migrated (~5 more pages)
- [ ] Consistent visual design across all empty states
- [ ] All empty states have icons, titles, descriptions
- [ ] Contextual messaging for filtered results
- [ ] Accessibility requirements met
- [ ] Design guidelines documented
- [ ] All tests pass
- [ ] Visual regression check complete

## Estimated Timeline

- Phase 1: 3 hours
- Phase 2: 5 hours
- Phase 3: 4 hours
- Phase 4: 2 hours
- Phase 5: 2 hours
- **Total: ~16 hours** (revised from initial 15h estimate)

## Testing Checklist

For each migrated page:
- [ ] Empty state displays correctly
- [ ] Icon is appropriate and visible
- [ ] Title is clear and concise
- [ ] Description is helpful
- [ ] CTA button works (if present)
- [ ] Responsive on mobile
- [ ] Accessible via keyboard
- [ ] Readable by screen reader

## Priority Order

**High Priority (Do First):**
1. HomePage - most visible
2. OffersPage / NeedsPage - core features (already mostly done)
3. ExchangesPage - important for functionality
4. MessagesPage - common use case

**Medium Priority:**
5. CellDetailPage - member-facing
6. MessageThreadPage - active conversations
7. AgentsPage - improving existing

**Lower Priority:**
8. RapidResponsePage - less frequently empty
9. KnowledgePage - supplementary feature
10. DiscoveryPage - search context

## Notes

- OffersPage and NeedsPage already have decent empty states from recent fixes
- May need minimal updates to use new component for consistency
- Focus on pages that currently have text-only empty states
- Consider adding illustrations in future enhancement
