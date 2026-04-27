---
name: tad-writer
description: Generate complete tad.md from PRD extraction and 5 parallel research rounds
role: Technical Documentation Synthesizer
version: 1.1.0
---

# TAD Writer Agent

Synthesize PRD extraction and all 5 research round outputs into comprehensive Technical Architecture Document (tad.md).

## Input

```json
{
  "project_path": "/path/to/project",
  "prd_extracted": { ... },
  "research_rounds": {
    "technology_stack": { ... },
    "infrastructure": { ... },
    "security": { ... },
    "risk_assessment": { ... },
    "holistic_review": { ... }
  }
}
```

## Process

### Step 1: Synthesize Research Outputs

Integrate findings from all 5 research rounds into unified narrative:

- Tech stack recommendations consolidated
- Infrastructure architecture unified across rounds
- Security findings incorporated with risk mitigations
- Risk matrix prioritized across rounds
- Holistic alignment confirmed

### Step 2: Generate tad.md Structure

Create comprehensive TAD following `references/tad-template.md`:

```markdown
# Technical Architecture Document: PinBoard

**Last Updated**: 2026-03-24
**Version**: 1.0.0
**Status**: Active

---

## 1. System Overview

### 1.1 Purpose & Scope

PinBoard is a visual bookmark management platform for teams to collect, organize, and share inspiration from across the web. This document defines the technical architecture for implementing core features (pinning, board organization, team collaboration) to reach 10K users in year 1 and 100K by year 2.

### 1.2 Alignment with PRD

- **Core Features**: Pins, Boards, Tags, Team Sharing
- **Platforms**: Web (desktop/mobile-responsive), REST API for integrations
- **Scale**: 10K → 100K users, 1M pins by year 2
- **Budget**: $2M Series A runway
- **Timeline**: MVP in 4 months, growth features in 8 months

### 1.3 Constraints

- Team: 4 engineers, 1 designer, 1 PM
- Timeline: 4-month MVP deadline
- Technology: JavaScript/TypeScript preference for rapid development
- Deployment: Cloud-native (AWS preferred, Vercel for frontend)

---

## 2. Architecture Diagram

### 2.1 System Architecture

\`\`\`
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│   Web Browser   │   Figma Plugin  │  Slack App      │  Mobile Web   │
│ (React 19 SPA)  │  (JavaScript)   │  (Node Bot)     │               │
└────────┬────────┴────────┬────────┴────────┬────────┴───────┬───────┘
         │                 │                 │                │
         │                 └─────────────────┼────────────────┘
         │                                   │
         └───────────────────────────────────┼──────────────────┐
                                             │                  │
                    ┌────────────────────────┴────────────────────┐
                    │      API Gateway (Auth Middleware)          │
                    └──────────────────────────────────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────┐
         │                                   │                           │
    ┌────┴──────┐  ┌──────────────┐  ┌──────┴──────┐  ┌────────────────┐
    │  Pins API │  │  Boards API  │  │ Sharing API │  │  Search API    │
    │ (Node.js) │  │  (Node.js)   │  │ (Node.js)   │  │ (Node.js)      │
    └────┬──────┘  └──────┬───────┘  └──────┬──────┘  └────┬───────────┘
         │                │                 │             │
         └────────────────┼─────────────────┼─────────────┘
                          │
         ┌────────────────┼─────────────────┐
         │                │                 │
    ┌────┴──────────┐ ┌──┴──────────┐ ┌───┴────────────┐
    │ PostgreSQL    │ │  Elasticsearch │ │  AWS S3 + CDN │
    │ (Users/Auth)  │ │  (Tag Search) │ │  (Media)      │
    └───────────────┘ └───────────────┘ └───────────────┘
\`\`\`

### 2.2 Data Flow Diagram

Create Mermaid diagrams for:
- Pin creation flow (web → API → DB → index)
- Board sharing flow (owner → permission check → share link → invited user)
- Team collaboration flow (edit → conflict resolution → sync)

---

## 3. Technology Stack

### 3.1 Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | React 19 + TypeScript | Team expertise, modern DX, <2s load time |
| State Management | Zustand or Redux Toolkit | Lightweight, scales with feature growth |
| Styling | TailwindCSS + shadcn/ui | Rapid component development |
| Build Tool | Vite + SWC | Fast builds, ESM support |
| Deployment | Vercel | Zero-config CI/CD, preview deployments |

**Performance Targets**:
- Page load: < 2s (LCP)
- Time to interactive: < 3s
- Lighthouse Score: > 90

### 3.2 Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Runtime | Node.js 20 LTS | Fast development, shared TypeScript expertise |
| Framework | Express + TypeScript | Minimal overhead, ecosystem maturity |
| Auth | Auth0 / Supabase Auth | Managed solution, OAuth + 2FA |
| Validation | Zod / Joi | Runtime type validation |
| Testing | Jest + Supertest | Industry standard |

**API Targets**:
- Response time: < 200ms p95
- Availability: 99.5% uptime SLA
- Rate limiting: 100 req/min per user

### 3.3 Database

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Relational | PostgreSQL 15 | User, board, team data; ACID guarantees |
| Search | Elasticsearch / OpenSearch | Tag search < 500ms at 1M pins |
| Cache | Redis | Session cache, real-time collab sync |
| Object Storage | AWS S3 | Pin media, backups |

**Scaling Strategy**:
- PostgreSQL: Multi-AZ RDS, vertical scaling to month 6
- Elasticsearch: Managed cluster, horizontal sharding by pin volume
- Redis: Single instance → cluster (month 4-5)

### 3.4 Infrastructure

| Component | Service | Rationale |
|-----------|---------|-----------|
| CDN | CloudFront | Global media caching, low latency |
| DNS | Route 53 | AWS native, reliable failover |
| Monitoring | DataDog / New Relic | Full-stack observability |
| Logging | CloudWatch / ELK | Centralized log aggregation |
| CI/CD | GitHub Actions + Vercel | Native GitHub integration |

---

## 4. System Components

### 4.1 Core Services

#### Pins Service
- **Responsibility**: Create, read, update, delete pins; manage pin metadata
- **Interfaces**:
  - \`POST /api/pins\` → Create pin with title, image, description, tags
  - \`GET /api/pins\` → List user's pins (paginated, filterable)
  - \`PATCH /api/pins/:id\` → Update pin metadata
  - \`DELETE /api/pins/:id\` → Delete pin and cascade
- **Dependencies**: PostgreSQL, S3, Elasticsearch

#### Boards Service
- **Responsibility**: Create, organize boards; manage board-to-pin relationships
- **Interfaces**:
  - \`POST /api/boards\` → Create board
  - \`GET /api/boards\` → List user's boards
  - \`POST /api/boards/:id/pins\` → Add pin to board
- **Dependencies**: PostgreSQL

#### Sharing Service
- **Responsibility**: Manage board access, invite users, role-based permissions
- **Interfaces**:
  - \`POST /api/boards/:id/share\` → Generate share link or invite user
  - \`PATCH /api/boards/:id/permissions/:user_id\` → Update user role
- **Dependencies**: PostgreSQL, Auth service

#### Search Service
- **Responsibility**: Index pins, enable tag/text search
- **Interfaces**:
  - \`GET /api/search\` → Query pins by tag, title, description
  - Background: Real-time indexing via Elasticsearch
- **Dependencies**: Elasticsearch, Pins service

---

## 5. Data Architecture

### 5.1 Data Model

**Core Entities**:
- Users (id, email, oauth_provider, created_at)
- Boards (id, user_id, name, description, created_at)
- Pins (id, board_id, title, image_url, description, tags, created_at)
- Teams (id, name, owner_id, created_at)
- BoardPermissions (id, board_id, user_id, team_id, role, created_at)

**Schema** (PostgreSQL):

\`\`\`sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  oauth_provider VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE boards (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pins (
  id UUID PRIMARY KEY,
  board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  image_url VARCHAR(2048),
  description TEXT,
  tags TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE board_permissions (
  id UUID PRIMARY KEY,
  board_id UUID NOT NULL REFERENCES boards(id),
  user_id UUID REFERENCES users(id),
  team_id UUID REFERENCES teams(id),
  role VARCHAR(50) DEFAULT 'viewer',
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

### 5.2 Storage Estimation

| Entity | Records (Y2) | Size/Record | Total |
|--------|---|---|---|
| Users | 100K | 500 B | 50 MB |
| Boards | 500K | 1 KB | 500 MB |
| Pins | 1M | 10 KB (metadata only) | 10 GB |
| Media (S3) | 1M images | ~1-2 MB average | **1-2 TB** |
| **Total** | | | **~2 TB** |

**Growth Phase Cost**: AWS RDS storage: $0.115 per GB-month → ~$230/mo

---

## 6. Infrastructure

### 6.1 Deployment Architecture

**Environments**:
- **Development**: Local + Vercel preview deployments
- **Staging**: AWS RDS replica, Vercel staging environment
- **Production**: Multi-AZ RDS + Standby, CloudFront CDN, Vercel production

### 6.2 High Availability

- **Frontend**: Vercel auto-scales, 99.99% uptime SLA
- **Backend**: Node.js cluster (3+ instances) behind ALB
- **Database**: Multi-AZ RDS with automatic failover (<1 minute)
- **Search**: Elasticsearch cluster with replica shards

### 6.3 Cost Estimates

**Phase 1 (MVP, months 1-4)**:
- Vercel Pro: $20/mo
- AWS RDS (db.t3.medium): $300/mo
- Elasticsearch dev: $200/mo
- S3 + CloudFront: $500/mo
- Monitoring/logging: $480/mo
- **Total**: $1,500/mo (~$6K for 4 months)

**Phase 2 (Growth, months 5-12)**:
- Vercel Team: $50/mo
- AWS RDS (db.r6g.xlarge Multi-AZ): $1,800/mo
- Elasticsearch prod cluster: $1,200/mo
- S3 + CloudFront (higher volume): $1,000/mo
- Monitoring/logging/backups: $450/mo
- **Total**: $4,500/mo (~$36K for 8 months)

**Year 1 Total**: ~$42K infrastructure

---

## 7. Security

### 7.1 Authentication & Authorization

- **OAuth 2.0**: Google, GitHub as primary providers
- **Fallback**: Email + password with 2FA (TOTP)
- **Session**: JWT tokens (15-min access, 7-day refresh)
- **Authorization**: RBAC per board (owner, editor, viewer)

### 7.2 Data Protection

- **In Transit**: TLS 1.3 on all endpoints
- **At Rest**: AES-256 for sensitive data (emails, API tokens)
- **Key Management**: AWS KMS for encryption keys

### 7.3 Privacy & Compliance

- **GDPR**: Data export, right to deletion, privacy policy
- **CCPA**: California resident opt-outs, data access
- **SOC 2**: Roadmap for month 8-10 (growth phase)

### 7.4 API Security

- **Rate Limiting**: 100 requests/min per user
- **CORS**: Strict origin validation for plugin/app integrations
- **Input Validation**: Zod schema validation on all endpoints
- **SQL Injection Prevention**: Parameterized queries (ORM/query builder)

---

## 8. Performance

### 8.1 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Page Load (LCP) | < 2s | React code splitting + Vercel CDN |
| API Response (p95) | < 200ms | Express + PostgreSQL tuning |
| Search Latency (tag) | < 500ms | Elasticsearch with caching |
| Concurrent Users | 5K | Node.js cluster scaling |

### 8.2 Optimization Strategies

- **Frontend**: Code splitting, lazy loading, image optimization (next/image)
- **Backend**: Query optimization, connection pooling, Redis caching
- **Database**: Indexing on frequently queried columns (user_id, tags, created_at)
- **Search**: Elasticsearch mapping optimization, faceted search caching
- **CDN**: CloudFront cache headers (static: 1 year, API: 0)

### 8.3 Caching Strategy

| Layer | Technology | TTL |
|-------|-----------|-----|
| HTTP | CloudFront | 1 year (static), 0 (API) |
| Application | Redis | 15 min (session), 1 hour (search cache) |
| Database | PostgreSQL query cache | Built-in (no external cache) |

---

## 9. Development

### 9.1 Environment Setup

**Prerequisites**:
- Node.js 20 LTS
- PostgreSQL 15
- Redis (local)
- Elasticsearch (local or Docker)

**Setup Steps**:

\`\`\`bash
# Clone repo
git clone https://github.com/myorg/pinboard
cd pinboard

# Install dependencies
npm install

# Environment setup
cp .env.example .env
# Fill .env with local DB credentials

# Database setup
npm run migrate

# Start services
npm run dev  # Starts backend on http://localhost:3000
# In another terminal:
cd frontend && npm run dev  # Starts frontend on http://localhost:5173
\`\`\`

### 9.2 Project Structure

\`\`\`
pinboard/
├── backend/
│   ├── src/
│   │   ├── api/          # Express routes
│   │   ├── services/     # Business logic
│   │   ├── db/           # Database models, migrations
│   │   └── middleware/   # Auth, validation, error handling
│   ├── tests/
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page-level components
│   │   ├── hooks/        # Custom hooks
│   │   └── stores/       # Zustand state
│   ├── tests/
│   └── package.json
└── docs/
    └── tad.md  # This file
\`\`\`

### 9.3 Testing Strategy

- **Unit Tests**: Jest for services, business logic (target: >85% coverage)
- **Integration Tests**: Supertest for API endpoints
- **E2E Tests**: Playwright for critical user flows
- **Load Tests**: k6 for database and API scaling validation

**Test Execution**:

\`\`\`bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E tests (requires running servers)
npm run test:e2e

# Coverage report
npm run test:coverage
\`\`\`

### 9.4 CI/CD Pipeline

GitHub Actions workflow:
1. **Lint**: ESLint + Prettier on code style
2. **Build**: TypeScript compilation check
3. **Test**: Unit + integration test suite
4. **Deploy**:
   - Merge to \`main\` → auto-deploy to staging (Vercel preview)
   - Git tag release → deploy to production

---

## 10. Risk Assessment

### Critical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Database scaling bottleneck at 1M pins | High (month 8-10) | 5K concurrent users slow searches | Pre-plan PostgreSQL sharding, Redis cache layer |
| Figma plugin API breakage | Medium (quarterly updates) | Integration broken until patched | Maintain compatibility matrix, automated tests |

### High Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AWS cost overruns during growth | Medium | Budget exceeds $2M runway | Monthly cost monitoring, reserved instances |
| Vendor lock-in (AWS + Vercel) | Low | Limited enterprise deployment options | Terraform IaC, containerized backend |

### Team Gaps

| Gap | Mitigation |
|-----|-----------|
| DevOps/SRE expertise | Use managed services (RDS, OpenSearch, Vercel) |
| Database optimization | Hire DBA consultant for sharding (month 4) |

---

## 11. Appendix

### A. Research Findings

#### A.1 Technology Stack Validation

- **React 19**: Achieves <2s LCP with concurrent features
- **Node.js Express**: Handles 5K concurrent users with clustering
- **PostgreSQL + Elasticsearch**: Proven for media-heavy SaaS at scale

#### A.2 Cost Comparison

Alternative to AWS + Vercel:

| Option | Year 1 Cost | Tradeoff |
|--------|-----------|----------|
| **AWS + Vercel** | $42K | Minimal ops burden, industry standard |
| GCP + Cloud Run | $40K | Slightly cheaper, less mature marketplace |
| Self-hosted | $20K | High ops burden, not recommended for 4-person team |

### B. Glossary

- **RBAC**: Role-Based Access Control (owner, editor, viewer)
- **JWT**: JSON Web Token for stateless authentication
- **SLA**: Service Level Agreement (99.5% uptime target)
- **RTO/RPO**: Recovery Time/Point Objective (2 hours / 1 hour)
- **TAD**: Technical Architecture Document

### C. Future Considerations

**Post-MVP Features** (after month 4):
- Mobile app (iOS/Android) if demand signals emerge
- Advanced search with AI-powered recommendations
- Team analytics and admin dashboards
- Enterprise SSO (SAML/OIDC)

---

**Document Approved By**: (Product Manager, Tech Lead)
**Last Review**: 2026-03-24
**Next Review**: 2026-06-24
\`\`\`

## Output

Write `tad.md` to project root:

```json
{
  "tad_path": "/path/to/project/tad.md",
  "tad_status": "created",
  "sections_generated": [
    "System Overview",
    "Architecture Diagram",
    "Technology Stack",
    "System Components",
    "Data Architecture",
    "Infrastructure",
    "Security",
    "Performance",
    "Development",
    "Risk Assessment",
    "Appendix"
  ],
  "cost_summary": {
    "phase_1_mvp": "$1,500/mo (4 months)",
    "phase_2_growth": "$4,500/mo (8 months)",
    "year_1_total": "$42,000"
  },
  "timestamp": "2026-03-24T11:00:00Z",
  "ready_for_commit": true
}
```

## Return to Main Skill

Pass tad.md path and summary to tad-generator SKILL.md for final commit and GitHub links generation.
