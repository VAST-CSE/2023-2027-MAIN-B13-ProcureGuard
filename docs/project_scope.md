# Project Scope & Architecture Roadmap

## 1. System Vision
The **Intelligent Procurement Verification and Supply Risk Prediction System** is designed to automate invoice reconciliation, detect procurement anomalies, and predict supply chain disruption risks before financial commitments or operational bottlenecks occur.

---

## 2. Core Governance Principles
- **Human-in-the-Loop Autonomy**: The system acts as an intelligent decision-support assistant. Discrepancies are surfaced objectively to aid human auditors.
- **Strictly Non-Accusatory Classification**: Discrepancies are **never labeled as fraud, theft, or illicit behavior**. Discrepancies are categorized strictly as operational variances (e.g., `QUANTITY_MISMATCH`, `PRICE_MISMATCH`, `DATA_VALIDATION_ERROR`) and marked for human verification.
- **Auditable & Explainable**: Every discrepancy includes explicit context—showing expected values, actual values, source fields, and clear non-technical rationale.

---

## 3. Current Implementation (Phase 1 Foundation)

The current phase establishes the deterministic verification baseline:

### Components Implemented
- **3-Way Verification Engine (`app/verification/engine.py`)**:
  - Compares Purchase Orders (PO), Goods Received Notes (GRN), and Supplier Invoices.
  - Validates document references (`po_number` cross-referencing).
  - Verifies supplier identity consistency across all three records.
  - Reconciles item identifiers.
  - Compares quantities across all three lifecycle stages:
    - Ordered vs Received (identifies under-deliveries and over-deliveries).
    - Invoiced vs Received (identifies over-billing and partial billings).
    - Invoiced vs Ordered (identifies unauthorized volume increases).
  - Compares PO agreed unit prices against invoiced unit prices with tolerance support.
  - Detects missing, empty, or negative values.
  - Outputs structured `VerificationResult` and `Discrepancy` objects.
  - Guarantees every discrepancy is flagged with `requires_human_review = True`.
- **Pure Standard Library Architecture**:
  - Built using Python 3 standard library (`dataclasses`, `decimal`, `enum`, `typing`, `unittest`).
  - No external third-party dependencies required for core logic.
- **Automated Verification Test Suite (`tests/test_engine.py`)**:
  - 100% test coverage over matching transactions, quantity mismatches, price mismatches, missing data, reference mismatches, and compliance with anti-fraud labeling rules.

---

## 4. Planned Future Features & Roadmap

```
+--------------------------------------------------------------------------+
|                        Current: Phase 1 (Baseline)                       |
|   Deterministic 3-Way Matching Engine & Discrepancy Reporting (Complete) |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
|                     Phase 2: Ingestion & Document Parsing                |
|   PDF Invoice OCR, CSV/Excel Batch Ingestion, Schema Normalization        |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
|                     Phase 3: AI Supply Risk Prediction                   |
|   Lead-Time Delay Risk, Supplier Reliability Scoring, Anomaly Detection  |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
|                 Phase 4: Human Review & Workflow Console                 |
|   Discrepancy Resolution Workspace, Audit Logs, Officer Approvals        |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
|                     Phase 5: Enterprise Integration                      |
|   FastAPI REST Microservice, ERP Connectors (SAP/Oracle), Event Queues   |
+--------------------------------------------------------------------------+
```

### Phase 2: Ingestion & Document Parsing
- OCR extraction pipeline for scanned PDF supplier invoices and paper delivery slips.
- Heuristic and LLM-assisted field mapping for varied vendor layouts.
- Support for multi-item line item matrices and partial fulfillment shipments.

### Phase 3: AI Supply Risk Prediction
- Predictive models for supplier delivery lead-time slippage.
- Dynamic vendor risk profiling based on historical variance frequencies, dispute history, and fulfillment consistency.
- Early warning alerts for potential stockouts or supply chain volatility.

### Phase 4: Human Review Workflow & UI
- Interactive reviewer workspace allowing procurement specialists to approve, dispute, or adjust line-item variances.
- Complete regulatory audit trail recording who reviewed each flagged item and the resolution rationale.

### Phase 5: Enterprise Integration & Production Readiness
- RESTful API endpoints powered by FastAPI.
- Relational database schema (PostgreSQL) for transactional persistence.
- Connector modules for enterprise ERP systems (SAP, Oracle NetSuite, Microsoft Dynamics).
