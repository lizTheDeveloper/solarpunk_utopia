# Solarpunk Mesh Network - Frontend

The unified React TypeScript frontend application for the Solarpunk Gift Economy Mesh Network.

## Overview

This is a production-ready, offline-first web application that brings together all six backend systems into a cohesive gift economy platform:

- **ValueFlows Node** - Offers, needs, exchanges, and economic events
- **DTN Bundle System** - Delay-tolerant networking and bundle propagation
- **Discovery & Search** - Distributed indexing and search across the mesh
- **File Chunking** - Knowledge sharing with resilient file distribution
- **Bridge Management** - Network topology and island connectivity
- **AI Agent System** - Autonomous assistants with human oversight

## Features

### Core Pages

- **Home** - Dashboard with system overview and quick actions
- **Offers** - Browse and create offers with filtering and search
- **Needs** - View and express needs with category filters
- **Exchanges** - Track exchanges and matched offers/needs
- **Discovery** - Distributed search across the mesh network
- **Knowledge** - Upload and download files, community library
- **Network** - Monitor network health, bridges, and bundle stats
- **AI Agents** - Manage autonomous agents and review proposals

### Design Principles

- **Solarpunk Aesthetic** - Green color palette emphasizing sustainability
- **Offline-First** - Shows bundle status and sync information
- **Simple UX** - <1 minute to create an offer (as per spec)
- **Community-Focused** - Mutual aid over transactions
- **Transparent** - Clear indication of data sources (local, cached, DTN)

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Full type safety
- **React Router** - Client-side routing
- **TanStack Query** - Server state management
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **date-fns** - Date formatting

## Project Structure

```
src/
├── api/              # API clients for all backend services
│   ├── dtn.ts
│   ├── valueflows.ts
│   ├── discovery.ts
│   ├── files.ts
│   ├── bridge.ts
│   └── agents.ts
├── components/       # Reusable UI components
│   ├── Card.tsx
│   ├── Button.tsx
│   ├── Loading.tsx
│   ├── ErrorMessage.tsx
│   ├── Layout.tsx
│   ├── Navigation.tsx
│   ├── OfferCard.tsx
│   ├── NeedCard.tsx
│   ├── MatchCard.tsx
│   ├── ProposalCard.tsx
│   ├── BundleStatus.tsx
│   └── NetworkStatus.tsx
├── hooks/            # Custom React hooks
│   ├── useOffers.ts
│   ├── useNeeds.ts
│   ├── useExchanges.ts
│   ├── useDiscovery.ts
│   ├── useFiles.ts
│   ├── useBundles.ts
│   ├── useBridge.ts
│   └── useAgents.ts
├── pages/            # Page components
│   ├── HomePage.tsx
│   ├── OffersPage.tsx
│   ├── NeedsPage.tsx
│   ├── CreateOfferPage.tsx
│   ├── CreateNeedPage.tsx
│   ├── ExchangesPage.tsx
│   ├── DiscoveryPage.tsx
│   ├── KnowledgePage.tsx
│   ├── NetworkPage.tsx
│   └── AgentsPage.tsx
├── types/            # TypeScript type definitions
│   ├── valueflows.ts
│   ├── bundles.ts
│   ├── discovery.ts
│   ├── files.ts
│   ├── network.ts
│   └── agents.ts
├── utils/            # Utility functions
│   ├── formatters.ts
│   ├── categories.ts
│   └── validation.ts
├── App.tsx           # Root component with routing
├── main.tsx          # Application entry point
└── index.css         # Global styles
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend services running (or configured API proxies)

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start dev server (http://localhost:3000)
npm run dev
```

The dev server includes automatic API proxying:
- `/api/dtn` → http://localhost:8000
- `/api/vf` → http://localhost:8001
- `/api/bridge` → http://localhost:8002
- `/api/discovery` → http://localhost:8003
- `/api/files` → http://localhost:8004

### Production Build

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

The build outputs to `dist/` directory.

## API Integration

All API calls go through centralized clients in `src/api/`. The dev server proxies these to backend services:

```typescript
// Example: Using the ValueFlows API
import { valueflowsApi } from '@/api/valueflows';

const offers = await valueflowsApi.getOffers();
const newOffer = await valueflowsApi.createIntent({
  type: 'offer',
  agent_id: 'user-123',
  resource_specification_id: 'tomatoes',
  quantity: 5,
  unit: 'kg',
});
```

## Key Components

### Resource Categories

Hierarchical resource catalog in `src/utils/categories.ts`:
- Food & Produce
- Tools & Equipment
- Materials & Supplies
- Skills & Services
- Knowledge & Information
- Energy & Power
- Technology & Electronics
- Household Goods

### Custom Hooks

React Query-based hooks provide caching, revalidation, and optimistic updates:

```typescript
// Offers
const { data: offers, isLoading } = useOffers();
const createOffer = useCreateOffer();

// Network Status
const { data: networkStatus } = useNetworkStatus();

// AI Agents
const { data: agents } = useAgents();
const { data: proposals } = useProposals('pending');
```

### Form Validation

Centralized validation in `src/utils/validation.ts`:

```typescript
const validation = validateIntentForm({
  resourceSpecificationId: 'tomatoes',
  quantity: 5,
  unit: 'kg',
});

if (!validation.valid) {
  console.error(validation.errors);
}
```

## Styling

Tailwind CSS with custom Solarpunk theme:

```javascript
// tailwind.config.js
colors: {
  'solarpunk': {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
}
```

## Performance

- **Code splitting** - Route-based automatic splitting
- **React Query caching** - Smart caching with 1min stale time
- **Optimistic updates** - Immediate UI feedback
- **Lazy loading** - Components loaded on demand

## Accessibility

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Focus management
- Color contrast (WCAG AA)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Follow existing code patterns
2. Use TypeScript strictly
3. Keep components small and focused
4. Write meaningful commit messages
5. Test on multiple screen sizes

## Troubleshooting

### API Connection Issues

Check that backend services are running:
```bash
# DTN Bundle System
curl http://localhost:8000/bundles

# ValueFlows Node
curl http://localhost:8001/intents
```

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### Type Errors

```bash
# Run type check
npm run type-check
```

## License

Part of the Solarpunk Mesh Network project.

## Architecture Notes

This frontend is designed for resilient, community-scale deployments:

- **Offline-first** - Works without internet, syncs when available
- **Mobile-optimized** - Touch-friendly, works on phones
- **Low bandwidth** - Efficient API calls, local caching
- **Mesh-aware** - Shows network topology and bundle propagation
- **Human-in-the-loop AI** - All AI proposals require human approval

The UI emphasizes transparency about where data comes from (local, cached from neighbors, or fresh from the network) and the status of asynchronous operations (bundle delivery, file downloads).
