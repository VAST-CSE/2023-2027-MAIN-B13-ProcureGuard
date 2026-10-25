# Sample Procurement Data

This directory stores representative datasets and fixture files used to test and demonstrate the **Intelligent Procurement Verification and Supply Risk Prediction System**.

---

## Document Schemas

### 1. Purchase Order (PO)
The legally authorized commitment issued to a vendor.
```json
{
  "po_number": "PO-2026-001",
  "supplier_id": "SUP-GLOBAL-88",
  "item_id": "SKU-STEEL-BEAM-A1",
  "quantity": 100,
  "unit_price": 45.50,
  "currency": "USD"
}
```

### 2. Goods Received Note (GRN)
Warehouse confirmation of physical delivery and quantity received.
```json
{
  "grn_number": "GRN-2026-089",
  "po_number": "PO-2026-001",
  "supplier_id": "SUP-GLOBAL-88",
  "item_id": "SKU-STEEL-BEAM-A1",
  "quantity": 100
}
```

### 3. Supplier Invoice
Commercial bill submitted by the vendor requesting payment.
```json
{
  "invoice_number": "INV-2026-4501",
  "po_number": "PO-2026-001",
  "supplier_id": "SUP-GLOBAL-88",
  "item_id": "SKU-STEEL-BEAM-A1",
  "quantity": 100,
  "unit_price": 45.50,
  "currency": "USD"
}
```

---

## Benchmark Test Cases

| Scenario | PO Details | GRN Details | Invoice Details | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Match** | 100 units @ $45.50 | 100 units received | 100 units @ $45.50 | `MATCHED` (No discrepancies) |
| **Quantity Variance** | 100 units @ $45.50 | 100 units received | 120 units @ $45.50 | `REQUIRES_HUMAN_REVIEW` (Invoiced > Received) |
| **Price Variance** | 100 units @ $45.50 | 100 units received | 100 units @ $52.00 | `REQUIRES_HUMAN_REVIEW` (Price deviation) |
| **Reference Mismatch** | PO: `PO-2026-001` | PO: `PO-WRONG-REF` | PO: `PO-2026-001` | `REQUIRES_HUMAN_REVIEW` (GRN reference mismatch) |
| **Incomplete Data** | Missing price | Standard GRN | Standard Invoice | `REQUIRES_HUMAN_REVIEW` (Validation failure) |

---

## Planned Future Datasets
- Multi-line purchase orders and fractional shipments.
- Anonymized historical supplier performance records (delivery lead times, defect rates) for the Risk Prediction module.
- Synthetic noise datasets simulating OCR transcription errors and formatting anomalies.
