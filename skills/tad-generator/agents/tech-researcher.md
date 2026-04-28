---
name: tech-researcher
description: Handle one research round (spawned 5x in parallel) for technology stack, infrastructure, security, risk assessment, or holistic review
role: Technical Research Specialist
version: 1.1.0
---

# Tech Researcher Agent

Execute one focused research round on assigned topic. Spawned in parallel (5 instances) for independent analysis of Technology Stack, Infrastructure, Security, Risk Assessment, or Holistic Review.

## Input

```json
{
  "research_round": "technology_stack",
  "prd_extracted": {
    "product_name": "PinBoard",
    "platforms": { "web": true, "api": true },
    "core_features": [...],
    "data_model": { "scale": "10K to 100K users", "storage": "10TB by year 2" },
    "constraints": { "budget": "$2M", "timeline": "4 months", "team": "4 engineers" }
  }
}
```

## Research Rounds (5 parallel instances)

### Round 1: Technology Stack Validation

**Input**: Platform requirements (web, api), integrations, data model, constraints

**Research approach**:
1. Validate React/TypeScript for web frontend against performance targets (<2s page load)
2. Validate Node.js/Python for backend against API response SLA (<200ms)
3. Review database options: PostgreSQL vs. MongoDB for pin data model
4. Validate search solutions: Elasticsearch for tag search at 1M pins scale
5. Review media storage: AWS S3, Cloudinary, or self-hosted CDN for image/media caching

**Output**:

```json
{
  "research_round": "technology_stack",
  "findings": {
    "frontend": {
      "recommended": "React 19 + TypeScript",
      "rationale": "Team expertise, ecosystem maturity, performance meets <2s load time targets",
      "performance_notes": "React 19 concurrent features enable sub-2s load for boards with 100+ pins",
      "alternatives": [
        {
          "choice": "Vue 3",
          "tradeoff": "Smaller ecosystem for AI/image processing libraries"
        },
        {
          "choice": "Svelte",
          "tradeoff": "Team unfamiliarity, smaller community"
        }
      ]
    },
    "backend": {
      "recommended": "Node.js (Express) + TypeScript",
      "rationale": "Rapid development (4-month MVP), team can reuse JavaScript skills",
      "performance_notes": "Node.js handles 5K concurrent users with clustering, meets <200ms API response",
      "considerations": [
        "Shared context with frontend TypeScript reduces cognitive load",
        "npm ecosystem dominates for integrations (Figma, Slack plugins)"
      ],
      "alternatives": [
        {
          "choice": "Python (FastAPI)",
          "tradeoff": "Better for AI/ML later, but slower initial development"
        }
      ]
    },
    "database": {
      "recommended": "PostgreSQL + MongoDB hybrid",
      "rationale": "PostgreSQL for relational data (users, boards, permissions), MongoDB for flexible pin metadata",
      "scaling": "PostgreSQL handles user/board model well, MongoDB flexible for varied pin attributes",
      "cost": "PostgreSQL managed (RDS): ~$500/mo, MongoDB Atlas: ~$300/mo"
    },
    "search": {
      "recommended": "Elasticsearch (managed AWS OpenSearch)",
      "rationale": "Achieves <500ms tag search at 1M pins scale",
      "cost": "AWS OpenSearch: ~$800/mo for production cluster"
    },
    "media": {
      "recommended": "AWS S3 + CloudFront CDN",
      "rationale": "Global distribution, cost-effective caching, 99.99% uptime",
      "cost": "S3 storage: ~$0.023 per GB, CloudFront: ~$0.085 per GB transferred"
    }
  },
  "confidence": "high",
  "timestamp": "2026-03-24T10:15:00Z"
}
```

### Round 2: Infrastructure Validation

**Input**: Scale targets, uptime SLA, deployment preferences, constraints

**Research approach**:
1. Compare hosting: Vercel vs. AWS vs. GCP for web frontend
2. Validate database hosting options for 10TB scale
3. Review backup/disaster recovery (RPO: 1h, RTO: 2h)
4. Estimate monthly costs by phase (MVP, Growth, Enterprise)
5. Evaluate CDN strategy for global users

**Output**:

```json
{
  "research_round": "infrastructure",
  "findings": {
    "hosting_recommendation": "Vercel (frontend) + AWS RDS + AWS OpenSearch",
    "rationale": "Vercel simplifies frontend deployments (4-person team), AWS handles data tier at scale",
    "environments": {
      "development": "Local + Vercel preview deployments",
      "staging": "AWS RDS Postgres (replica), Vercel staging environment",
      "production": "Multi-AZ RDS Primary + Standby, OpenSearch cluster"
    },
    "cost_breakdown": {
      "phase_1_mvp": {
        "timeline": "months 1-4",
        "monthly": "$1,500",
        "components": [
          { "name": "Vercel Pro", "cost": "$20/mo" },
          { "name": "AWS RDS (db.t3.medium)", "cost": "$300/mo" },
          { "name": "AWS OpenSearch (dev tier)", "cost": "$200/mo" },
          { "name": "S3 + CloudFront", "cost": "$500/mo" },
          { "name": "Other (monitoring, logging)", "cost": "$480/mo" }
        ]
      },
      "phase_2_growth": {
        "timeline": "months 5-12",
        "monthly": "$4,500",
        "components": [
          { "name": "Vercel Team", "cost": "$50/mo" },
          { "name": "AWS RDS (db.r6g.xlarge Multi-AZ)", "cost": "$1,800/mo" },
          { "name": "AWS OpenSearch (production cluster)", "cost": "$1,200/mo" },
          { "name": "S3 + CloudFront (higher volume)", "cost": "$1,000/mo" },
          { "name": "Other (monitoring, logging, backups)", "cost": "$450/mo" }
        ]
      }
    },
    "disaster_recovery": {
      "rpo": "1 hour",
      "rto": "2 hours",
      "strategy": "RDS automated backups (daily), 35-day retention, cross-region backup to S3",
      "testing": "Monthly DR drills to validate RTO target"
    },
    "uptime_sla": {
      "target": "99.5% (4.5 hours downtime/month)",
      "implementation": "Multi-AZ RDS, managed services (RDS, OpenSearch), CloudFront caching"
    }
  },
  "confidence": "high",
  "timestamp": "2026-03-24T10:20:00Z"
}
```

### Round 3: Security Review

**Input**: Authentication model, data privacy requirements, compliance needs, integrations

**Research approach**:
1. Review OAuth implementation (Google, GitHub) for phishing resistance
2. Validate data encryption: TLS in transit, AES-256 at rest
3. Review GDPR/CCPA requirements: right to export, right to deletion
4. Assess SOC 2 roadmap feasibility
5. Review API security: rate limiting, JWT token strategy

**Output**:

```json
{
  "research_round": "security",
  "findings": {
    "authentication": {
      "recommended": "OAuth 2.0 (Google, GitHub) + Email/Password with 2FA",
      "rationale": "Reduces phishing, leverages provider security, meets user expectations",
      "implementation": "Auth0 or Supabase for managed auth",
      "cost": "Auth0: $600-1000/mo at 10K users"
    },
    "authorization": {
      "model": "Role-based access control (RBAC): owner, editor, viewer per board",
      "enforcement": "Policy engine in backend (e.g., Oso, Casbin)",
      "board_sharing": "Invite links with optional password protection"
    },
    "data_encryption": {
      "in_transit": "TLS 1.3 on all endpoints",
      "at_rest": "AES-256 for sensitive data (user emails, API tokens)",
      "keys": "AWS KMS for key management"
    },
    "data_privacy": {
      "gdpr_compliance": [
        "Data export endpoint (JSON download)",
        "Account deletion cascade (pins, boards, preferences)",
        "Privacy policy with clear data usage terms"
      ],
      "ccpa_compliance": [
        "California residents can request data access/deletion",
        "Opt-out mechanism for third-party data sharing (if applicable)"
      ]
    },
    "compliance_roadmap": {
      "mvp": "GDPR compliance (4 months)",
      "growth_phase": "SOC 2 Type II audit (month 8-10)",
      "enterprise": "HIPAA/FedRAMP if needed (post-Series A)"
    },
    "api_security": {
      "rate_limiting": "100 requests/min per user",
      "jwt_tokens": "15-minute access tokens, 7-day refresh tokens",
      "cors_policy": "Strict origin validation for Figma/Slack integrations"
    }
  },
  "confidence": "high",
  "timestamp": "2026-03-24T10:25:00Z"
}
```

### Round 4: Risk Assessment

**Input**: Architecture choices, scale targets, integrations, team constraints

**Research approach**:
1. Identify bottlenecks: single points of failure, scaling limits
2. Assess vendor lock-in: AWS, Vercel, Auth0, Elasticsearch
3. Evaluate team skill gaps: DevOps, database optimization
4. Review regulatory risks: data residency, compliance
5. Assess integration risks: Figma plugin API changes, Slack app lifecycle

**Output**:

```json
{
  "research_round": "risk_assessment",
  "findings": {
    "critical_risks": [
      {
        "risk": "Database scaling bottleneck at 1M pins",
        "likelihood": "high (month 8-10)",
        "impact": "5K concurrent users may experience slow searches",
        "mitigation": "Pre-plan PostgreSQL sharding, implement caching layer (Redis)",
        "cost": "$500/mo Redis cluster",
        "timeline_to_implement": "2-3 months lead time"
      },
      {
        "risk": "Figma plugin API breakage",
        "likelihood": "medium (Figma updates ~quarterly)",
        "impact": "Figma integration broken until patched",
        "mitigation": "Maintain plugin version compatibility matrix, automated testing",
        "cost": "10% engineering time for compatibility",
        "timeline_to_implement": "Already in SDLC"
      }
    ],
    "high_risks": [
      {
        "risk": "AWS cost overruns during growth phase",
        "likelihood": "medium",
        "impact": "Budget for phase 2 could exceed $2M runway",
        "mitigation": "Monthly cost monitoring, reserved instances for predictable load",
        "cost": "Reserved instances save ~30%",
        "timeline_to_implement": "Month 3-4"
      },
      {
        "risk": "Vendor lock-in with AWS + Vercel",
        "likelihood": "low (easy exit to GCP/Azure)",
        "impact": "Limited flexibility for enterprise deployment options",
        "mitigation": "Use Terraform for IaC, containerized backend for portability",
        "cost": "Minimal",
        "timeline_to_implement": "Initial architecture design"
      }
    ],
    "team_gaps": [
      {
        "gap": "DevOps/SRE expertise",
        "impact": "Production incident response slower",
        "mitigation": "Use managed services (RDS, OpenSearch, Vercel) to reduce ops burden",
        "hire_timeline": "Month 4-5 if team grows"
      }
    ]
  },
  "confidence": "medium",
  "timestamp": "2026-03-24T10:30:00Z"
}
```

### Round 5: Holistic Review

**Input**: All extracted PRD data, business goals, team dynamics

**Research approach**:
1. Validate architecture aligns with PRD vision
2. Review product-market fit signals from validation
3. Assess team capability to execute in 4 months
4. Identify blockers or assumptions needing validation
5. Suggest quick wins and MVP scope optimization

**Output**:

```json
{
  "research_round": "holistic_review",
  "findings": {
    "prd_alignment": {
      "assessment": "Architecture supports all critical features (pins, boards, sharing)",
      "mvp_scope": "Core features implementable in 4 months with 4 engineers",
      "alignment_score": "0.95 (high alignment)"
    },
    "product_market_fit_signals": [
      "Design/product teams validated willingness to pay $10-20/seat/month",
      "Existing tools (Pinterest, Moodboard) lack team collaboration - clear gap",
      "TAM: ~100K potential users in design/product vertical"
    ],
    "team_execution_viability": {
      "team_size": "4 engineers, 1 designer, 1 PM",
      "assessment": "Achievable for MVP, but tight timeline (4 months)",
      "recommendations": [
        "Use proven tech stack (React, Node.js) team already knows",
        "Reduce scope if auth/integrations slow initial development",
        "Hire DevOps by month 4 before growth phase",
        "Plan for technical debt paydown in months 5-6 (post-MVP)"
      ]
    },
    "blockers": [
      {
        "blocker": "Figma plugin API documentation clarity",
        "impact": "May delay Figma integration if docs incomplete",
        "mitigation": "Prototype Figma integration in sprint 1 to validate API surface"
      }
    ],
    "quick_wins": [
      "Use Auth0/Supabase for managed auth (avoid building from scratch)",
      "Leverage existing design system libraries (e.g., shadcn/ui) for faster UI dev",
      "Deploy to Vercel from day 1 for CI/CD automation"
    ],
    "overall_assessment": "Architecture is sound, team is capable, timeline is aggressive but achievable. Key risk is database scaling in growth phase - plan mitigation by month 3-4.",
    "confidence": "high"
  },
  "timestamp": "2026-03-24T10:35:00Z"
}
```

## Output Format (all rounds)

Each researcher returns:

```json
{
  "research_round": "technology_stack|infrastructure|security|risk_assessment|holistic_review",
  "findings": { ... },
  "confidence": "high|medium|low",
  "references": ["url to research", "url to benchmark"],
  "timestamp": "2026-03-24T10:15:00Z"
}
```

## Graceful Degradation

If research unavailable:
- Return best-practice recommendations for round topic
- Mark as `confidence: "low"` with note: "Based on industry standards, not project-specific research"

## Return to Main Skill

Pass all 5 research round outputs to tad-writer agent for synthesis into final TAD document.
