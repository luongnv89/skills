---
name: prd-reader
description: Read PRD and supporting docs, return structured extraction for architecture research
metadata:
  role: "Requirements Extractor"
  version: "1.1.0"
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

If `idea.md` exists: target audience, goals, and Technical Context (stack, timeline, team, budget, constraints).

If `validate.md` exists: the Quick Verdict, Concerns, Competitive Landscape (including Open-source Alternatives and Build vs. Base Recommendation), Technical Risk, and Implementation Roadmap.

### Step 3: Generate Structured Extraction

Return comprehensive JSON extraction:

```json
{
  "project_path": "<from prd.md, or null>",
  "extraction_timestamp": "<from prd.md, or null>",
  "product": {
    "name": "<from prd.md, or null>",
    "vision": "<from prd.md, or null>",
    "target_users": [
      "<from prd.md, or null>"
    ],
    "target_scale": "<from prd.md, or null>"
  },
  "core_features": [
    {
      "id": "<from prd.md, or null>",
      "name": "<from prd.md, or null>",
      "description": "<from prd.md, or null>",
      "priority": "<from prd.md, or null>",
      "complexity": "<from prd.md, or null>"
    }
  ],
  "platforms": {
    "web": {
      "required": "<from prd.md, or null>",
      "browsers": [
        "<from prd.md, or null>"
      ],
      "mobile_responsive": "<from prd.md, or null>"
    },
    "mobile": {
      "required": "<from prd.md, or null>",
      "ios": "<from prd.md, or null>",
      "android": "<from prd.md, or null>"
    },
    "api": {
      "required": "<from prd.md, or null>",
      "public": "<from prd.md, or null>",
      "partners": [
        "<from prd.md, or null>"
      ]
    }
  },
  "integrations": [
    {
      "service": "<from prd.md, or null>",
      "type": "<from prd.md, or null>",
      "purpose": "<from prd.md, or null>",
      "complexity": "<from prd.md, or null>"
    }
  ],
  "data_model": {
    "core_entities": [
      "<from prd.md, or null>"
    ],
    "user_growth": "<from prd.md, or null>",
    "pin_volume": "<from prd.md, or null>",
    "storage_per_pin": "<from prd.md, or null>",
    "estimated_storage": "<from prd.md, or null>"
  },
  "performance_requirements": {
    "page_load": "<from prd.md, or null>",
    "search_latency": "<from prd.md, or null>",
    "api_response": "<from prd.md, or null>",
    "concurrent_users": "<from prd.md, or null>"
  },
  "nonfunctional_requirements": {
    "authentication": "<from prd.md, or null>",
    "authorization": "<from prd.md, or null>",
    "data_privacy": "<from prd.md, or null>",
    "compliance": "<from prd.md, or null>",
    "uptime_sla": "<from prd.md, or null>",
    "disaster_recovery": "<from prd.md, or null>"
  },
  "constraints": {
    "budget": "<from prd.md, or null>",
    "timeline": "<from prd.md, or null>",
    "team_size": "<from prd.md, or null>",
    "deployment": "<from prd.md, or null>"
  },
  "success_metrics": [
    {
      "metric": "<from prd.md, or null>",
      "target_month_6": "<from prd.md, or null>",
      "target_month_12": "<from prd.md, or null>"
    }
  ],
  "assumptions_validated": [
    "<from prd.md, or null>"
  ],
  "assumptions_invalidated": [],
  "open_questions": [
    "<from prd.md, or null>"
  ],
  "research_areas_needed": [
    "<from prd.md, or null>"
  ]
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
