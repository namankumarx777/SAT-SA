# SENTRA Engineering Hardening Report

## Overview
This document tracks the Phase 13 production-grade engineering hardening of the SENTRA application. The goal is to elevate the application from a working prototype to a defensible offline security application.

## Audit Matrix

### 1. Input Validation & Path Traversal (API Layer)
- [ ] **Risk Identification**: Endpoints in `blockchain.py`, `ingestion.py`, `rules.py`, `supervisory_risk.py`, etc., accept file paths and entity IDs directly from request bodies/query params without sufficient validation or path resolution bounds checking.
- [ ] **Mitigation Plan**:
  - Implement a `safe_resolve_path(base_dir, requested_path)` utility to ensure paths do not traverse outside designated boundaries (`REPO_ROOT / "data"`).
  - Add strict Pydantic constraints to all API models (e.g., `max_length`, `pattern` for entity IDs and dataset IDs).
  - Ensure `filename` in uploads cannot be exploited or overwrite critical files.

### 2. Error Handling & Security Exceptions
- [ ] **Risk Identification**: Bare exceptions are being caught and converted to string messages in 500 and 422 HTTP responses. This can leak stack traces or internal filesystem structures.
- [ ] **Mitigation Plan**:
  - Implement a centralized error handling middleware or FastAPI exception handlers.
  - Return sanitized, user-friendly error codes (e.g., `INTERNAL_ERROR`, `INVALID_PATH`) without exposing underlying implementation details.

### 3. Resource Exhaustion & Payload Limits
- [ ] **Risk Identification**: File uploads (`ingestion.py`) do not have enforced size limits in the code. Analytics endpoints process entire parquet files into memory indiscriminately.
- [ ] **Mitigation Plan**:
  - Enforce max upload size via middleware or stream reading constraints.
  - Implement basic pagination or bounds checking on large JSON responses from the analytics store.
  - Implement basic rate limiting or concurrency limits on heavy analytical operations to prevent local denial of service.

### 4. Concurrency Safety & Data Integrity
- [ ] **Risk Identification**: While ingestion uses atomic directory replacement (`.replace()`), the analytical engines (rules, gaps, risk) write directly to the output directories sequentially. If an error occurs midway, partial datasets are left behind.
- [ ] **Mitigation Plan**:
  - Update all analytics engine write paths to use a temporary directory pattern (similar to ingestion), followed by an atomic rename `replace()`.

### 5. Logging & Observability
- [ ] **Risk Identification**: Missing structured logging across the application. Operations happen silently.
- [ ] **Mitigation Plan**:
  - Integrate a structured logging library (e.g., `structlog` or `logging` with JSON formatting).
  - Add middleware to log all incoming requests, status codes, and execution times.
  - Add explicit logging in critical paths (e.g., file writes, blockchain commits).

### 6. Dependency Hygiene & Secrets Management
- [ ] **Risk Identification**: No explicit checks for dependency vulnerabilities. Hardcoded configurations.
- [ ] **Mitigation Plan**:
  - Audit `requirements.txt` and package.json for outdated or vulnerable packages.
  - Ensure all configuration settings use environment variables with fallback defaults, validating through `pydantic-settings`.

### 7. Frontend Security
- [ ] **Risk Identification**: Potential XSS in raw data displays, lack of strict CSP, and error leakages to the UI.
- [ ] **Mitigation Plan**:
  - Audit Next.js React components for `dangerouslySetInnerHTML` and ensure HTML sanitization.
  - Add secure headers (Helmet/Next headers configuration).

## Next Steps
This matrix will be executed systematically following the approval of the implementation plan.
