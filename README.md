# Intelligent Procurement System

An intelligent procurement verification and supply risk prediction system designed to automate invoice reconciliation (3-way matching) and identify supply chain vulnerabilities.

---

## Features (Phase 1)
- **Deterministic 3-Way Matching**: Cross-compares Purchase Orders (PO), Goods Received Notes (GRN), and Supplier Invoices.
- **Reference & Identity Checks**: Validates agreement of PO numbers and supplier IDs across all documents.
- **Variance Detection**: Pinpoints discrepancies in quantities (under-delivery, over-delivery, over-invoicing) and unit pricing.
- **Data Validation**: Identifies missing, empty, or negative values.
- **Human-in-the-Loop Governance**: Discrepancies are **never** labeled as fraud; every discrepancy is objectively formatted and flagged for human review.
- **Zero Third-Party Dependencies**: Pure Python 3 standard library implementation.

---

## Project Structure

```
intelligent-procurement-system/
├── app/
│   ├── __init__.py
│   ├── server.py              # Lightweight stdlib HTTP server & /api/verify
│   └── verification/
│       ├── __init__.py
│       └── engine.py           # Core 3-way matching verification engine
├── frontend/
│   ├── index.html             # Single-page application with dashboard & views
│   ├── css/
│   │   └── style.css          # Modern responsive CSS design system
│   └── js/
│       ├── app.js             # UI controller & interaction logic
│       ├── api.js             # API connector to Python verification engine
│       └── sample_data.js     # Benchmark packages and transparent demo risk data
├── tests/
│   ├── __init__.py
│   └── test_engine.py          # Unit tests covering all matching scenarios
├── sample_data/
│   └── README.md               # Data schema specifications and benchmark cases
├── docs/
│   └── project_scope.md        # Current implementation vs planned roadmap
├── .gitignore
└── README.md
```

---

## Quickstart & Running Tests

### 1. Activate the Virtual Environment

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 2. Launch the Web Frontend

To launch the web interface with live Python verification:

```powershell
python app/server.py
```

Then open your browser to:
**[http://localhost:8000](http://localhost:8000)**

*Note: You can also directly double-click or open `frontend/index.html` in any web browser without running a server; the frontend includes a standalone fallback.*

### 3. Run the Unit Test Suite

Run all tests via Python's built-in `unittest` runner:

```powershell
python -m unittest discover tests
```

To run with verbose output:

```powershell
python -m unittest -v tests/test_engine.py
```

---

## Basic Python Example

```python
from app.verification import (
    VerificationEngine,
    PurchaseOrder,
    GoodsReceivedNote,
    SupplierInvoice,
)

engine = VerificationEngine()

po = PurchaseOrder(
    po_number="PO-2026-001",
    supplier_id="SUP-88",
    item_id="SKU-STEEL-A1",
    quantity=100,
    unit_price=45.50,
)

grn = GoodsReceivedNote(
    grn_number="GRN-2026-089",
    po_number="PO-2026-001",
    supplier_id="SUP-88",
    item_id="SKU-STEEL-A1",
    quantity=100,
)

invoice = SupplierInvoice(
    invoice_number="INV-2026-4501",
    po_number="PO-2026-001",
    supplier_id="SUP-88",
    item_id="SKU-STEEL-A1",
    quantity=120,   # Invoiced quantity exceeds received quantity
    unit_price=45.50,
)

result = engine.verify(po, grn, invoice)

print(f"Matched: {result.is_match}")
print(f"Status: {result.status.value}")
for disc in result.discrepancies:
    print(f"- [{disc.type.value}] {disc.message} (Requires Review: {disc.requires_human_review})")
```

---

## Roadmap

See [docs/project_scope.md](docs/project_scope.md) for the complete multi-phase architecture roadmap including document ingestion, AI supply risk prediction, and enterprise ERP integration.
