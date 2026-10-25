"""
Unit tests for the VerificationEngine component.

Covers:
  - Fully matching transaction (PO, GRN, and Invoice consistent)
  - Invoice quantity exceeding received quantity
  - Unit price mismatch between PO and Invoice
  - Missing or malformed required data
  - Supplier reference mismatch
  - PO reference mismatch
  - Verification that discrepancies are never labeled as fraud and always flagged for human review
  - Plain dictionary input compatibility
"""

import unittest
from decimal import Decimal

from app.verification.engine import (
    DiscrepancyType,
    GoodsReceivedNote,
    PurchaseOrder,
    SupplierInvoice,
    VerificationEngine,
    VerificationStatus,
)


class TestVerificationEngine(unittest.TestCase):
    """Test suite for 3-way matching and discrepancy detection."""

    def setUp(self):
        """Initialize verification engine and baseline valid records."""
        self.engine = VerificationEngine()
        self.valid_po = PurchaseOrder(
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=100,
            unit_price=45.50,
            currency="USD",
        )
        self.valid_grn = GoodsReceivedNote(
            grn_number="GRN-2026-089",
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=100,
        )
        self.valid_invoice = SupplierInvoice(
            invoice_number="INV-2026-4501",
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=100,
            unit_price=45.50,
            currency="USD",
        )

    def test_fully_matching_transaction(self):
        """A transaction with matching references, quantities, and prices must pass verification."""
        result = self.engine.verify(self.valid_po, self.valid_grn, self.valid_invoice)

        self.assertTrue(result.is_match)
        self.assertEqual(result.status, VerificationStatus.MATCHED)
        self.assertEqual(len(result.discrepancies), 0)
        self.assertIn("successful", result.summary.lower())

    def test_invoice_quantity_exceeding_received_quantity(self):
        """When invoice quantity exceeds received goods, flag quantity discrepancy for human review."""
        discrepant_invoice = SupplierInvoice(
            invoice_number="INV-2026-4502",
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=120,  # 120 invoiced vs 100 received
            unit_price=45.50,
        )

        result = self.engine.verify(self.valid_po, self.valid_grn, discrepant_invoice)

        self.assertFalse(result.is_match)
        self.assertEqual(result.status, VerificationStatus.REQUIRES_HUMAN_REVIEW)

        qty_discrepancies = [d for d in result.discrepancies if d.type == DiscrepancyType.QUANTITY_MISMATCH]
        self.assertGreaterEqual(len(qty_discrepancies), 1)

        # Ensure discrepancy specifically mentions invoiced quantity exceeding received quantity
        invoiced_vs_received = next(
            (d for d in qty_discrepancies if "exceeds received quantity" in d.message), None
        )
        self.assertIsNotNone(invoiced_vs_received)
        self.assertTrue(invoiced_vs_received.requires_human_review)
        self.assertEqual(invoiced_vs_received.expected, Decimal("100"))
        self.assertEqual(invoiced_vs_received.actual, Decimal("120"))

    def test_unit_price_mismatch(self):
        """When invoice unit price deviates from PO agreed price, flag price discrepancy."""
        discrepant_invoice = SupplierInvoice(
            invoice_number="INV-2026-4503",
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=100,
            unit_price=52.00,  # 52.00 vs PO price of 45.50
        )

        result = self.engine.verify(self.valid_po, self.valid_grn, discrepant_invoice)

        self.assertFalse(result.is_match)
        self.assertEqual(result.status, VerificationStatus.REQUIRES_HUMAN_REVIEW)

        price_discrepancies = [d for d in result.discrepancies if d.type == DiscrepancyType.PRICE_MISMATCH]
        self.assertEqual(len(price_discrepancies), 1)

        discrepancy = price_discrepancies[0]
        self.assertEqual(discrepancy.field, "invoice.unit_price")
        self.assertEqual(discrepancy.expected, Decimal("45.50"))
        self.assertEqual(discrepancy.actual, Decimal("52.00"))
        self.assertTrue(discrepancy.requires_human_review)
        self.assertIn("Marked for human review", discrepancy.message)

    def test_missing_required_data(self):
        """When required fields are missing or empty, identify validation errors and mark for review."""
        incomplete_po = {
            "po_number": "",  # Missing PO number
            "supplier_id": "SUP-GLOBAL-88",
            "item_id": "SKU-STEEL-BEAM-A1",
            "quantity": 100,
            "unit_price": None,  # Missing unit price
        }

        result = self.engine.verify(incomplete_po, self.valid_grn, self.valid_invoice)

        self.assertFalse(result.is_match)
        self.assertEqual(result.status, VerificationStatus.REQUIRES_HUMAN_REVIEW)

        validation_errors = [d for d in result.discrepancies if d.type == DiscrepancyType.DATA_VALIDATION_ERROR]
        self.assertGreaterEqual(len(validation_errors), 2)

        fields_with_errors = [d.field for d in validation_errors]
        self.assertIn("PO.po_number", fields_with_errors)
        self.assertIn("PO.unit_price", fields_with_errors)

    def test_invalid_negative_numeric_data(self):
        """Negative quantity or price must trigger validation errors."""
        invalid_po = PurchaseOrder(
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=-10,  # Negative quantity
            unit_price=45.50,
        )

        result = self.engine.verify(invalid_po, self.valid_grn, self.valid_invoice)
        self.assertFalse(result.is_match)
        val_errors = [d for d in result.discrepancies if d.type == DiscrepancyType.DATA_VALIDATION_ERROR]
        self.assertTrue(any(d.field == "PO.quantity" for d in val_errors))

    def test_supplier_and_po_reference_mismatches(self):
        """Cross-document reference mismatches must be caught and structured."""
        mismatched_grn = GoodsReceivedNote(
            grn_number="GRN-2026-089",
            po_number="PO-WRONG-REF",
            supplier_id="SUP-WRONG-SUPPLIER",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=100,
        )

        result = self.engine.verify(self.valid_po, mismatched_grn, self.valid_invoice)

        self.assertFalse(result.is_match)
        types = [d.type for d in result.discrepancies]
        self.assertIn(DiscrepancyType.REFERENCE_MISMATCH, types)
        self.assertIn(DiscrepancyType.SUPPLIER_MISMATCH, types)

    def test_never_labels_discrepancy_as_fraud(self):
        """
        Verify compliance with the core ethical and governance standard:
        Discrepancies must NEVER be labeled as fraud; they must be marked for human review.
        """
        discrepant_invoice = SupplierInvoice(
            invoice_number="INV-2026-9999",
            po_number="PO-2026-001",
            supplier_id="SUP-GLOBAL-88",
            item_id="SKU-STEEL-BEAM-A1",
            quantity=500,  # Huge variance
            unit_price=999.00,  # Huge price surge
        )

        result = self.engine.verify(self.valid_po, self.valid_grn, discrepant_invoice)
        result_dict = result.to_dict()

        serialized = str(result_dict).lower()
        self.assertNotIn("fraud", serialized)
        self.assertNotIn("fraudulent", serialized)
        self.assertNotIn("scam", serialized)
        self.assertNotIn("theft", serialized)

        # Confirm all discrepancies require human review
        for disc in result.discrepancies:
            self.assertTrue(disc.requires_human_review)
            self.assertIn("human review", disc.message.lower())

    def test_dict_input_support(self):
        """The engine must seamlessly accept plain Python dictionaries."""
        po_dict = {
            "po_number": "PO-2026-DICTS",
            "supplier_id": "SUP-99",
            "item_id": "ITEM-1",
            "quantity": "50.0",
            "unit_price": "12.50",
            "currency": "USD",
        }
        grn_dict = {
            "grn_number": "GRN-2026-DICTS",
            "po_number": "PO-2026-DICTS",
            "supplier_id": "SUP-99",
            "item_id": "ITEM-1",
            "quantity": "50.0",
        }
        inv_dict = {
            "invoice_number": "INV-2026-DICTS",
            "po_number": "PO-2026-DICTS",
            "supplier_id": "SUP-99",
            "item_id": "ITEM-1",
            "quantity": "50.0",
            "unit_price": "12.50",
            "currency": "USD",
        }

        result = self.engine.verify(po_dict, grn_dict, inv_dict)
        self.assertTrue(result.is_match)
        self.assertEqual(result.status, VerificationStatus.MATCHED)


if __name__ == "__main__":
    unittest.main()
