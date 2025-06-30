# MVP Development Plan

## Overview
This plan outlines the high-level steps, required staff, and estimated timeline to deliver a Minimum Viable Product (MVP) of the data analysis platform in the customer's GCP environment.

---

## Required Staff
- **Project Manager / Product Owner**
- **CloudOps/DevOps Engineer** (general cloud project setup)
- **Backend Developer** (Python, FastAPI, API design, Streamlit/Gradio)
- **ML Engineer** (LLM ideas evaluation, implementation, benchmarking)

## Optional Staff:
- **Frontend Developer** (React/Vue)
- **Security Engineer** (IAP, IAM, AD/LDAP integration if not handled by devops)
- **QA** (solution testing, but could be done by backend enigneer)
---

## High-Level Execution Plan

### 1. **Project Setup & Planning** (1-2 week) 
- Define MVP scope, user stories, and acceptance criteria. Reevaluate if the problem cen be solved without generative AI tooling
- Evaluate data compliance in terms of external Gen-AI processing (may be a need of deploying inhouse LLM instance)
- Set up project management tools and communication channels.
- Provision initial GCP project and environments.

### 2.1 **CI/CD & Infrastructure Foundation** (0.5-1 week)
- Set up GitHub repository and branching strategy.
- Configure GitHub Actions for CI/CD.
- Set up GCP Artifact Registry for Docker images.
- Provision Cloud Run and App Engine environments.
- Establish VPC, IAM roles, and service accounts.

### 2.2. **Authentication & Security** (0.5-1 week)
- Integrate Google Identity-Aware Proxy (IAP) for frontend and backend.
- Connect IAP to customer's Active Directory/LDAP for group-based access.
- Test access control and user provisioning.

### 2.3. **LLM workflow engine** (2-3 weeks)
- Establish metrics and benchmark results
- Consider various solution tests such as: enrichment with dataprofiling metadata, LLM as a judge or self-reflection
- Revisit development plan after solution testing
- Implement LangGraph-based workflow engine for orchestrating analysis.
- Integrate with LLM API (OpenAI or other) for analysis tasks.

### 3.1. **Backend** (1-1.5 weeks)
- Develop FastAPI backend with endpoints for data info, analysis, and history.
- Implement database access and result storage.
- Write unit and integration tests.
- Provision Cloud SQL (Postgres/MySQL) or connect to customer's preferred database (BigQuery, Redshift, etc.).

### 3.2. **Frontend Development** (1-1.5 weeks)
- Draft a UI proposal
- Option A: Build a simple UI using Streamlit or Gradio for rapid MVP delivery.
- Option B: Build a React/Vue frontend for richer UI (if required).
- Integrate with backend API for analysis and data display.
- Implement authentication flow with IAP.

### 4. **Testing & QA** (0.5-1 week)
- Conduct end-to-end testing (functionality, security, and performance).
- User acceptance testing (UAT) with customer stakeholders.
- Fix bugs and polish UX.

### 5. **Deployment & Handover** (1 week)
- Finalize CI/CD for production deployment.
- Deploy MVP to customer's GCP environment.
- Provide documentation and basic training.
- Handover to customer IT/operations team.

---

## Estimated Timeline
- **Total Duration:** 8-10 weeks (assuming some parallelization and no major blockers)

---

## Notes
- Timeline may vary based on customer requirements, data complexity, and integration needs.
- Early use of low-code frontend (Streamlit/Gradio) can accelerate MVP delivery.
- Security and compliance reviews should be included as part of QA and deployment.
- Backend engineer could be potentially replaced by an ML Engineer as the solution seems to be simple.
- The core team consists of DevOps and Backend/ML Engineers. Front-end engineers, security engineers depend on the customer needs and how role responsibilities are defined.