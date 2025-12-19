# Tasks: GAP-10 Exchange Completion

## Implementation (3-4 hours)

### Task 1: Add completeExchange API method
**File**: `frontend/src/api/valueflows.ts`
**Estimated**: 30 minutes

```typescript
export const completeExchange = async (exchangeId: string) => {
  const response = await api.post(`/vf/exchanges/${exchangeId}/complete`);
  return response.data;
};
```

### Task 2: Update ExchangesPage UI
**File**: `frontend/src/pages/ExchangesPage.tsx`
**Estimated**: 2 hours

```typescript
const upcomingExchanges = exchanges?.filter(e => e.status !== 'completed');
const pastExchanges = exchanges?.filter(e => e.status === 'completed');

// Show "Mark Complete" button for user's role
{exchange.provider_id === currentUser.id && !exchange.provider_confirmed && (
  <button onClick={() => markComplete(exchange.id)}>
    ✓ Mark Complete
  </button>
)}
```

### Task 3: Add useExchanges hook
**File**: `frontend/src/hooks/useExchanges.ts`
**Estimated**: 1 hour

```typescript
const useCompleteExchange = () => {
  const queryClient = useQueryClient();
  return useMutation(
    (exchangeId: string) => completeExchange(exchangeId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['exchanges']);
        toast.success('Exchange marked complete!');
      }
    }
  );
};
```

### Task 4: Add celebration/confirmation
**Estimated**: 30 minutes

Show success toast or modal with celebration message.

**Total: 4 hours**
