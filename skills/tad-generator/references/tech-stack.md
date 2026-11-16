# Technical stacks — requirements & best practices

This document describes general requirements and best practices when choosing and defining a technical stack for a software project. It is structured so you can quickly pick the guidance relevant to the type of project you're building: a library (Python/JavaScript), a full-stack web app, a RESTful API server, serverless functions, data/ML pipelines, or a mobile app. Each section lists recommended concerns, common libraries/tools, and a short checklist to use when planning or reviewing the stack.

Every list here is a set of options, not a default. Choose each technology from the PRD's constraints and the Phase 3 research; no vendor or stack is preferred.

Keep these high-level principles in mind across all project types:

- Minimal surface area: pick the smallest set of well-supported, actively maintained dependencies that satisfy requirements.
- Reproducibility: pin versions, use lockfiles and reproducible build artifacts (wheels, npm lock, Docker images).
- Developer experience (DX): fast local setup, good docs, and clear dev/test commands.
- Security by design: dependency scanning, least privilege for credentials, secrets management, and secure defaults.
- Observability: logging, metrics, and error tracking from day one.
- CI/CD and automation: automated tests, linting, and gated deploys.
- Licensing: ensure dependencies' licenses are compatible with your distribution model.

---

## Python library / package

Use case: a reusable library distributed to other applications or the Python Package Index (PyPI).

Key requirements:

- Packaging: source distribution (sdist) and wheels. Use pyproject.toml (PEP 517/518) and modern build backends (setuptools, poetry, or flit).
- Dependency management: uv, poetry, or pip-tools. List runtime dependencies separately from dev dependencies and commit a lockfile for reproducible tests (for example: uv lockfile, poetry.lock, or pip-tools generated lockfiles).
- Testing: pytest with coverage, tests that run fast and in isolation.
- Type hints: use mypy or pyright for static typing; include type stubs if needed.
- CI: run tests on multiple Python versions, run linters and type checks.
- Documentation: README with quick start, API reference (Sphinx or mkdocs), and examples.
- Distribution: sign packages, publish to PyPI or internal index, maintain versioning (semver or calendar versioning).

- Environment: use virtual environments for Python development (venv, virtualenv, or conda) and record the workflow in README. Avoid committing the venv directory.
- Configuration: store runtime configuration in a `.env` file for secrets/local overrides and a separate config file (e.g., config.toml, config.yaml or config.py) for structured defaults. Use a library like python-dotenv to load `.env` in development.
- Logging: implement structured logging and write logs to rotating files for later debugging (use Python logging.handlers.RotatingFileHandler or TimedRotatingFileHandler). Ensure logs include timestamps, levels, request ids (for web apps), and enough context to trace issues.

- Common tools & libraries:

- Packaging / dependency management: uv, poetry, flit, setuptools + wheel
- Testing: pytest, hypothesis (property tests)
- Linting: black, isort, flake8
- Types: mypy, pyright
- CI: GitHub Actions, GitLab CI, CircleCI
- Security: bandit (static security checks), pip-audit

Checklist:

- [ ] pyproject.toml with build-system declared
- [ ] tests + CI matrix for target Python versions
- [ ] type checking integrated in CI
- [ ] documentation build and examples
- [ ] reproducible lockfile and changelog for releases
 - [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)
 - [ ] virtual environment documented and used for development
 - [ ] `.env` + config file pattern documented and example provided
 - [ ] logging implemented and configured to write to files (rotating) for debugging

---

## JavaScript library

Use case: reusable package published to npm or consumed internally.

Key requirements:

- Language: JavaScript or TypeScript. TypeScript gives consumers type declarations; plain JavaScript skips a build step.
- Module formats and targets: decide on ESM vs CommonJS and document the chosen format. Prefer ESM for modern projects.
- Bundling: avoid unnecessary bundling for libraries — prefer shipped source with clear exports. If bundling is required, use Rollup or esbuild.
- Testing: unit tests (Jest, Vitest), browser and Node environment testing if required.
- Linting and formatting: ESLint and Prettier with a consistent config.
- CI: test and lint across Node versions.

Common tools & libraries:
- Build: esbuild, Rollup
- Testing: Jest, Vitest
- Linting: ESLint, Prettier
- Publishing: npm, pnpm, yarn; use semantic-release for automated releases

Checklist:

- [ ] Clear package.json exports field
- [ ] CI with tests and linting
- [ ] Lockfile (package-lock.json, pnpm-lock.yaml)
- [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

Style & linting: pick one shared ESLint baseline (for example Airbnb, standard, or the framework's own config) and apply it to every package.

---

## Full-stack web application (frontend + backend)

Use case: web application with user-facing frontend and a backend/API.

Key requirements and architecture decisions:

- Monorepo vs separate repos: for tightly coupled teams, a monorepo can simplify coordination; for independent teams, separate repos reduce blast radius.
- Frontend framework: React/Next.js, Vue/Nuxt, SvelteKit, or server-rendered templates when the UI is simple. Styling: Tailwind CSS, CSS modules, or a component library.
- State management: the framework's built-in state first; Redux Toolkit, Zustand, Pinia, or similar when shared client state grows.
- Backend: Node.js (Express, NestJS), Python (FastAPI, Django), Go, Java (Spring Boot), or a backend-as-a-service; REST or GraphQL by the clients' needs.
- Data storage: choose the database based on requirements: relational (PostgreSQL, MySQL, or managed Postgres such as Supabase), document (MongoDB), or SQLite for small projects and prototypes.
- Authentication & Authorization: server sessions, tokens (JWT), or a managed auth provider. Document the session or token lifecycle, rotation and revocation strategy.
- APIs: design with OpenAPI (Swagger) and version your API.
- Deployment: containers (Docker) orchestrated by Kubernetes or managed services (Vercel for frontend; Heroku, Fly.io, Render, Cloud Run for backend).
- Observability: structured logs, request tracing (OpenTelemetry), metrics (Prometheus + Grafana), and error tracking (Sentry).
- Performance: caching (CDN for static assets, Redis for data caching), background jobs (Bull for Node), and rate limiting.

Common tools & libraries:
- Frontend: React/Next.js, Vue/Nuxt, SvelteKit
- Backend: FastAPI, Django, Express, NestJS, Spring Boot, Go Gin
- DB & managed services: Supabase (managed Postgres + auth), PostgreSQL, Redis, MongoDB
- Third-party services: Resend (transactional email), Stripe (payments)
- Storage / CDN: Cloudflare R2 (S3-compatible object store + edge capabilities)
- Infra: Docker, Kubernetes, Terraform / Pulumi for infra as code
- CI/CD / Hosting: GitHub Actions, GitLab CI, CircleCI, Cloudflare Pages (fast frontend builds + edge deploys)

Bootstrap with the chosen framework's official scaffolder (for example `npm create vite@latest`, `create-next-app`, `django-admin startproject`), then add the lint, format and test scripts the developer bootstrap runs.

Checklist:

- [ ] Architecture diagram (components, data flow, treatment of secrets)
- [ ] CI/CD pipelines for frontend and backend
- [ ] Automated tests (unit, integration, e2e) and code coverage targets
- [ ] Static analysis, dependency scanning, and security policy
- [ ] Monitoring/alerting / SLOs defined
- [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

---

## RESTful API server (microservice)

Use case: small-to-medium independent service exposing business logic via HTTP/JSON.

Key requirements:

- API design: OpenAPI contract, clear error model, versioning and backward compatibility plan.
- Runtime: choose by the team's skills and the workload (Node.js, Python, Go, Java); prefer async patterns and middleware-based design.
- Data storage and migrations: use a robust migration tool (for SQL: knex or prisma migrate; for MongoDB: migrate-mongo or native migration patterns).
- Observability: request logs, structured fields (request id), distributed tracing.
- Resilience: timeouts, retries with exponential backoff, circuit breakers if applicable.
- Authentication: tokens (JWT), API keys, or mTLS between services; document token handling and revocation.

Common tools & libraries:

- Frameworks: FastAPI (Python), Express/Nest (Node), Spring Boot (Java), Gin (Go)
- Data layer: SQLAlchemy/Prisma/TypeORM/Knex
- Migrations: Alembic, Flyway, prisma migrate
- Docs: OpenAPI/Swagger UI

Checklist:

- [ ] OpenAPI spec and generated clients if helpful
- [ ] Health checks and readiness/liveness probes
- [ ] Rate limiting and authentication middleware
- [ ] CI that runs contract tests (if clients exist)
- [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

---

## Serverless functions / FaaS

Use case: event-driven or infrequently used endpoints where scaling to zero reduces costs.

Key requirements:

- Cold-start considerations: prefer lightweight runtimes or provisioned concurrency for latency-sensitive functions.
- Idempotency: ensure event handlers are idempotent or detect/handle duplicates.
- Packaging and size: minimize bundle size, vendor only what's needed.
- Local dev and testing: use local emulators or frameworks with good dev DX (Serverless Framework, AWS SAM, Vercel Functions).

Common tools:

- Platforms: AWS Lambda (with API Gateway), Google Cloud Functions, Azure Functions, Vercel, Netlify
- Frameworks: Serverless Framework, Architect, AWS SAM, Pulumi/Terraform for infra

Checklist:

- [ ] Function-level observability (traces and logs)
- [ ] Secrets stored in secure manager (AWS Secrets Manager, Parameter Store)
- [ ] CI pipeline that deploys and runs integration tests
 - [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

---

## Data pipelines and ML systems

Use case: batch or streaming ETL, feature pipelines, model training and model-serving.

Key requirements:

- Reproducibility: data versioning (DVC, Delta Lake), environment reproducibility (conda, poetry, Docker), and fixed random seeds for experiments.
- Separation of concerns: separate ingestion, transformation, training, and serving layers.
- Scheduling and orchestration: Airflow, Prefect, Dagster for DAG coordination.
- Monitoring: data quality checks, model drift detection, and lineage tracking.
- Resource management: GPU-enabled training environments, spot instances for cost control, and autoscaling for inference.

Common tools & frameworks:

- Batch/stream: Apache Spark, Flink, Beam
- Orchestration: Airflow, Prefect, Dagster
- Model infra: MLflow, TFX, BentoML, Seldon Core
- Storage: S3, GCS, Delta Lake, BigQuery, Redshift

Checklist:

- [ ] Data contracts and schema checks
- [ ] Experiment tracking and reproducible runs
- [ ] CI for data pipelines (unit tests for transforms)
- [ ] Model evaluation and validation gates before deploy
 - [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

---

## Mobile apps (iOS / Android / cross-platform)

Use case: native or cross-platform mobile application.

Key requirements:

- Native vs Cross-platform: choose native (Swift/Kotlin) for platform-specific performance or cross-platform (React Native, Flutter) for faster development across both platforms.
- CI/CD: automated builds, signing, and distribution to test channels (TestFlight, Firebase App Distribution) and app stores.
- Offline-first: plan for intermittent connectivity and local caching/sync.
- Analytics and crash reporting: e.g., Sentry, Firebase Crashlytics.

Common tools:

- Native: Xcode, Android Studio
- Cross-platform: React Native, Flutter
- Backend: GraphQL (Apollo), or REST API, push notifications (FCM/APNs)

Checklist:

- [ ] Automated builds and signing in CI
- [ ] Crash reporting and analytics enabled
- [ ] Security review for storage and permissions
 - [ ] developer bootstrap: provide a single, documented command or script that installs dependencies and runs linting, formatting, tests, and an optional static security scan (where available)

---

## Cross-cutting concerns (applies to every project)

- CI/CD: every repository should have pipeline code to run tests, linters, static analysis, build artifacts, and promote releases.
- Secrets & config: never store secrets in source. Use environment variables and a secrets manager. Keep runtime config separate from code.
- Backups & DR: plan backups for databases and critical storage. Test restore procedures regularly.
- Licensing & legal: document third-party license usage and comply with redistribution rules.
- Team knowledge: onboard docs, architecture decision records (ADR), and runbooks for incidents.

- Developer bootstrap: provide a single, documented command (for example `./dev.sh bootstrap`, `make bootstrap`, or `npm run setup`) that installs dependencies, runs linters/formatters, runs tests, and optionally runs a quick static security scan. Recommended tools to enable this include `make`, small bootstrap scripts, task runners (just, npm scripts), or language-native CLIs (uv, poetry, pnpm).

- Hosting & CDN: managed edge platforms (Cloudflare Pages, Vercel, Netlify) suit static frontends; S3-compatible object stores (AWS S3, Cloudflare R2, Google Cloud Storage) serve assets. Document the bucket lifecycle, access controls, and caching rules in the deployment docs.

Examples: .env loading and logging to files

Node.js (load .env + file logging with winston):

```javascript
// load .env
require('dotenv').config();
const winston = require('winston');

const logger = winston.createLogger({
	level: process.env.LOG_LEVEL || 'info',
	format: winston.format.json(),
	transports: [
		new winston.transports.Console(),
		new winston.transports.File({ filename: 'logs/app.log', maxsize: 1024 * 1024 * 10 })
	]
});

module.exports = logger;
```

Python (load .env + rotating file logs):

```python
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import os

load_dotenv()
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

logger = logging.getLogger('app')
logger.setLevel(LOG_LEVEL)
handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('logger configured')
```