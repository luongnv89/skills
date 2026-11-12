---
name: prd-reader
description: Read PRD and supporting docs, return structured extraction for architecture research
role: Requirements Extractor
version: 1.1.0
---

# PRD Reader Agent

Read Product Requirements Document and supporting context files, returning structured extraction of requirements and constraints for TAD research.

## Input

```json
{
  "project_path": "/path/to/project",
  "prd_file": "prd.md",
  "supporting_docs": ["idea.md", "validate.md"]
}
```

## Process

### Step 1: Read PRD Document

Parse `prd.md` and extract:

**Core Information**:
- Product name
- Vision/purpose statement
- Target users/audience
- Core features (listed, prioritized)
- Success metrics/KPIs

**Technical Requirements**:
- Platform: web, mobile, API, desktop, etc.
- Integration points: third-party APIs, services
- Data requirements: storage volume, types
- Performance requirements: latency, throughput
- Scalability targets: users, requests per second

**Constraints**:
- Budget (if mentioned)
- Timeline
- Team size
- Deployment platform (if specified)

**Non-Functional Requirements**:
- Authentication/authorization model
- Data privacy requirements (GDPR, CCPA, etc.)
- Compliance needs (SOC 2, HIPAA, etc.)
- Uptime/SLA requirements
- Disaster recovery needs

### Step 2: Read Supporting Documents

If `idea.md` exists:
- Extract market research findings
- Competitor analysis points
- User pain points
- Validation results

If `validate.md` exists:
- User feedback summary
- Validated vs. invalidated assumptions
- Refined feature priorities

### Step 3: Generate Structured Extraction

Return comprehensive JSON extraction:

```json
{
  "project_path": "/path/to/project",
  "extraction_timestamp": "2026-03-24T10:00:00Z",
  "product": {
    "name": "PinBoard",
    "vision": "Visual bookmark management platform for teams to collect, organize, and share inspiration",
    "target_users": ["designers", "product managers", "creative teams"],
    "target_scale": "10,000 users year 1, 100,000 users by year 2"
  },
  "core_features": [
    {
      "id": 1,
      "name": "Pin Creation & Management",
      "description": "Users can save links, images, notes as pins",
      "priority": "critical",
      "complexity": "high"
    },
    {
      "id": 2,
      "name": "Board Organization",
      "description": "Group pins into boards, organize by tags",
      "priority": "critical",
      "complexity": "medium"
    },
    {
      "id": 3,
      "name": "Team Collaboration",
      "description": "Share boards, collaborative curation, permissions",
      "priority": "high",
      "complexity": "high"
    }
  ],
  "platforms": {
    "web": {
      "required": true,
      "browsers": ["Chrome", "Firefox", "Safari", "Edge"],
      "mobile_responsive": true
    },
    "mobile": {
      "required": false,
      "ios": false,
      "android": false
    },
    "api": {
      "required": true,
      "public": false,
      "partners": ["Figma", "Slack"]
    }
  },
  "integrations": [
    {
      "service": "Figma",
      "type": "plugin",
      "purpose": "Direct pin save from Figma workspace",
      "complexity": "medium"
    },
    {
      "service": "Slack",
      "type": "app",
      "purpose": "Share boards in Slack channels",
      "complexity": "low"
    }
  ],
  "data_model": {
    "core_entities": ["users", "boards", "pins", "tags", "teams"],
    "user_growth": "10K to 100K users",
    "pin_volume": "1M pins by year 2",
    "storage_per_pin": "~10MB average (with caching)",
    "estimated_storage": "10TB by year 2"
  },
  "performance_requirements": {
    "page_load": "< 2 seconds for board view",
    "search_latency": "< 500ms for tag search across 1M pins",
    "api_response": "< 200ms for pin operations",
    "concurrent_users": "5,000 concurrent editing"
  },
  "nonfunctional_requirements": {
    "authentication": "OAuth with Google/GitHub, email/password",
    "authorization": "Role-based: owner, editor, viewer per board",
    "data_privacy": "GDPR compliant, user data export",
    "compliance": "SOC 2 Type II (target year 2)",
    "uptime_sla": "99.5% (4.5 hours downtime/month)",
    "disaster_recovery": "RPO: 1 hour, RTO: 2 hours"
  },
  "constraints": {
    "budget": "Series A: $2M runway",
    "timeline": "MVP in 4 months, Series A features in 8 months",
    "team_size": "4 engineers, 1 designer, 1 product manager",
    "deployment": "Prefer cloud (AWS/Vercel recommended)"
  },
  "success_metrics": [
    {
      "metric": "Monthly Active Users",
      "target_month_6": "5K",
      "target_month_12": "50K"
    },
    {
      "metric": "Pins per User",
      "target": "avg 100 pins/user"
    },
    {
      "metric": "Board Sharing Rate",
      "target": "30% of boards shared with teams"
    }
  ],
  "assumptions_validated": [
    "Teams spend 20% of workflow on visual inspiration collection",
    "Existing tools (Pinterest, Moodboard) lack team collaboration",
    "Design/product teams will pay $10-20/seat/month"
  ],
  "assumptions_invalidated": [],
  "open_questions": [
    "Mobile app timing - demand signals unclear",
    "Enterprise SSO requirements - confirm with first enterprise leads"
  ],
  "research_areas_needed": [
    "Technology Stack: Validate React/Node.js against storage/search scaling",
    "Infrastructure: AWS vs. Vercel for media-heavy content",
    "Security: Review encryption, compliance roadmap",
    "Risk Assessment: Identify bottlenecks, vendor dependencies",
    "Holistic Review: Ensure PRD alignment, startup feasibility"
  ]
}
```

## Output Requirements

Pass to tech-researcher agent for parallel research rounds:

```json
{
  "prd_extracted": true,
  "extraction_complete": true,
  "project": "PinBoard",
  "research_areas": [
    "Technology Stack",
    "Infrastructure",
    "Security",
    "Risk Assessment",
    "Holistic Review"
  ],
  "constraints": {
    "budget": "$2M runway",
    "timeline": "4 months MVP",
    "team": "4 engineers"
  },
  "data_model": {
    "core_entities": ["users", "boards", "pins", "tags", "teams"],
    "scale": "10K to 100K users",
    "storage": "10TB by year 2"
  },
  "ready_for_research": true,
  "timestamp": "2026-03-24T10:00:00Z"
}
```

## Graceful Degradation

If PRD file missing:
- Return error with clear instructions to provide prd.md
- Suggest minimum PRD structure user should follow

If supporting docs missing:
- Continue with core PRD only
- Mark as `supporting_docs_available: false`

## Return to Main Skill

Pass full extraction JSON to tad-generator SKILL.md for research phase initiation. Used by 5 parallel tech-researcher agent instances.
