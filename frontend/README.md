# Compliance OS - Frontend

Next.js 14 frontend application for Compliance OS V1.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn or pnpm

### Installation

1. **Install dependencies:**
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run development server:**
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

The application will be available at http://localhost:3000

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (dashboard)/        # Dashboard routes (group)
│   │   │   ├── dashboard/     # Executive Control Tower
│   │   │   ├── compliance/    # Compliance Calendar
│   │   │   └── evidence/      # Evidence Vault
│   │   ├── login/             # Login page
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── providers.tsx      # React Query provider
│   ├── components/
│   │   ├── layout/            # Layout components
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   └── ui/                # Reusable UI components
│   │       ├── Button.tsx
│   │       └── RAGBadge.tsx
│   ├── lib/
│   │   ├── api/               # API client and endpoints
│   │   │   ├── client.ts
│   │   │   └── endpoints.ts
│   │   └── store/             # Zustand stores
│   │       └── auth-store.ts
│   └── types/                 # TypeScript types
│       └── index.ts
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🎨 Styling

Using **TailwindCSS** for styling with custom RAG status colors:
- Green: `#10b981`
- Amber: `#f59e0b`
- Red: `#ef4444`

## 🔧 Key Technologies

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type safety
- **TailwindCSS**: Utility-first CSS
- **React Query**: Data fetching and caching
- **Zustand**: State management
- **Axios**: HTTP client
- **React Hook Form**: Form handling
- **Zod**: Schema validation

## 📝 Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run start`: Start production server
- `npm run lint`: Run ESLint
- `npm run type-check`: Run TypeScript type checking
- `npm run format`: Format code with Prettier

## 🚧 Implementation Status

### Implemented (Phase 2-3)
- [x] Authentication flow (login, logout, token refresh)
- [x] Dashboard with RAG status cards and overdue table
- [x] Compliance list view with filtering
- [x] Audit log viewer (role-restricted)
- [x] Form validation with React Hook Form + Zod (login)
- [x] E2E tests with Playwright

### Pending (Phase 6+)
- [ ] Protected route middleware
- [ ] Full dashboard layout with sidebar navigation
- [ ] Evidence vault with upload/download UI
- [ ] Workflow task management UI
- [ ] Entity and user management pages
- [ ] Compliance detail view
- [ ] Unit tests for components

## 🔐 Authentication

Authentication is handled via JWT tokens stored in localStorage (consider moving to httpOnly cookies for production).

The API client automatically:
- Adds `Authorization: Bearer <token>` header to requests
- Redirects to `/login` on 401 responses
- Refreshes tokens when needed

## 📚 API Integration

API endpoints are defined in `src/lib/api/endpoints.ts` and use the axios client configured in `src/lib/api/client.ts`.

Example usage:
```typescript
import { complianceInstancesApi } from '@/lib/api/endpoints'

// In a React component
const { data } = await complianceInstancesApi.list({
  entity_id: 'xxx',
  status: 'Overdue',
})
```

## 🎯 Next Steps (Phase 6)

1. Add Next.js middleware for protected routes
2. Build dashboard layout with sidebar navigation
3. Create evidence vault UI (list, filter, upload, download)
4. Build workflow task management interface
5. Add entity and user management pages
6. Implement compliance detail view with workflow
7. Add comprehensive error boundaries and loading states
