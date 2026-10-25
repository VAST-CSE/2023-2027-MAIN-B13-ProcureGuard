"""
Verification Engine for Three-Way Matching in Intelligent Procurement.

This module compares Purchase Orders (PO), Goods Received Notes (GRN), and Supplier
Invoices to detect reference mismatches, quantity variances, unit price discrepancies,
and missing or malformed required data.

Governance & Ethics Rule:
Discrepancies are NEVER labeled as fraud, malice, or illicit activity. All discrepancies
are treated as operational variances requiring human review and domain verification.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class DiscrepancyType(str, Enum):
    """Categorization of procurement variances requiring human review."""
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    SUPPLIER_MISMATCH = "SUPPLIER_MISMATCH"
    ITEM_MISMATCH = "ITEM_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"


class VerificationStatus(str, Enum):
    """Overall outcome of the 3-way matching process."""
    MATCHED = "MATCHED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


@dataclass(frozen=True)
class Discrepancy:
    """Represents a specific discrepancy identified during verification."""
    type: DiscrepancyType
    field: str
    message: str
    expected: Any
    actual: Any
    requires_human_review: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert discrepancy to dictionary representation."""
        return {
            "type": self.type.value,
            "field": self.field,
            "message": self.message,
            "expected": str(self.expected) if isinstance(self.expected, Decimal) else self.expected,
            "actual": str(self.actual) if isinstance(self.actual, Decimal) else self.actual,
            "requires_human_review": self.requires_human_review,
        }


@dataclass
class PurchaseOrder:
    """Purchase Order (PO) document record."""
    po_number: str
    supplier_id: str
    item_id: str
    quantity: Union[Decimal, float, int, str]
    unit_price: Union[Decimal, float, int, str]
    currency: str = "USD"


@dataclass
class GoodsReceivedNote:
    """Goods Received Note (GRN) document record."""
    grn_number: str
    po_number: str
    supplier_id: str
    item_id: str
    quantity: Union[Decimal, float, int, str]


@dataclass
class SupplierInvoice:
    """Supplier Invoice document record."""
    invoice_number: str
    po_number: str
    supplier_id: str
    item_id: str
    quantity: Union[Decimal, float, int, str]
    unit_price: Union[Decimal, float, int, str]
    currency: str = "USD"


@dataclass
class VerificationResult:
    """Comprehensive result of comparing PO, GRN, and Supplier Invoice."""
    is_match: bool
    status: VerificationStatus
    discrepancies: List[Discrepancy] = field(default_factory=list)
    summary: str = ""
    documents: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert verification result to dictionary representation."""
        return {
            "is_match": self.is_match,
            "status": self.status.value,
            "discrepancy_count": len(self.discrepancies),
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "summary": self.summary,
            "documents": self.documents,
        }


class VerificationEngine:
    """
    Core engine responsible for 3-way matching across PO, GRN, and Invoice.
    
    Verifies:
      1. Mandatory field presence and type sanity.
      2. Document and supplier reference consistency.
      3. Item identity agreement.
      4. Quantity reconciliation (ordered vs received vs invoiced).
      5. Unit price reconciliation (PO agreed price vs invoiced price).
      6. Currency agreement.
    """

    def __init__(self, price_tolerance: Union[Decimal, float, str] = "0.00", qty_tolerance: Union[Decimal, float, str] = "0.00"):
        """
        Initialize the engine with configurable numeric tolerances.
        
        Args:
            price_tolerance: Acceptable absolute price difference (default: 0.00).
            qty_tolerance: Acceptable absolute quantity difference (default: 0.00).
        """
        self.price_tolerance = Decimal(str(price_tolerance))
        self.qty_tolerance = Decimal(str(qty_tolerance))

    def _to_decimal(self, val: Any, field_name: str, doc_name: str, errors: List[Discrepancy]) -> Optional[Decimal]:
        """Safely convert numeric input to Decimal and validate positive value."""
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(Discrepancy(
                type=DiscrepancyType.DATA_VALIDATION_ERROR,
                field=f"{doc_name}.{field_name}",
                message=f"Missing required numeric value for '{field_name}' in {doc_name}. Marked for human review.",
                expected="positive number",
                actual=val,
            ))
            return None
        try:
            dec = Decimal(str(val))
            if dec < Decimal("0"):
                errors.append(Discrepancy(
                    type=DiscrepancyType.DATA_VALIDATION_ERROR,
                    field=f"{doc_name}.{field_name}",
                    message=f"Invalid negative value '{val}' for '{field_name}' in {doc_name}. Marked for human review.",
                    expected="non-negative number",
                    actual=val,
                ))
                return None
            return dec
        except (InvalidOperation, ValueError, TypeError):
            errors.append(Discrepancy(
                type=DiscrepancyType.DATA_VALIDATION_ERROR,
                field=f"{doc_name}.{field_name}",
                message=f"Invalid non-numeric value '{val}' for '{field_name}' in {doc_name}. Marked for human review.",
                expected="valid numeric value",
                actual=val,
            ))
            return None

    def _validate_required_string(self, val: Any, field_name: str, doc_name: str, errors: List[Discrepancy]) -> Optional[str]:
        """Validate that a required string attribute is present and non-empty."""
        if val is None or not str(val).strip():
            errors.append(Discrepancy(
                type=DiscrepancyType.DATA_VALIDATION_ERROR,
                field=f"{doc_name}.{field_name}",
                message=f"Missing or empty required field '{field_name}' in {doc_name}. Marked for human review.",
                expected="non-empty string",
                actual=val,
            ))
            return None
        return str(val).strip()

    def _normalize_doc(self, doc: Union[Dict[str, Any], Any], doc_type: str) -> Dict[str, Any]:
        """Normalize input to standard dictionary format."""
        if isinstance(doc, dict):
            return dict(doc)
        if hasattr(doc, "__dict__"):
            return vars(doc)
        raise ValueError(f"Unsupported document format for {doc_type}: {type(doc)}")

    def verify(
        self,
        po: Union[PurchaseOrder, Dict[str, Any]],
        grn: Union[GoodsReceivedNote, Dict[str, Any]],
        invoice: Union[SupplierInvoice, Dict[str, Any]],
    ) -> VerificationResult:
        """
        Perform a 3-way match across Purchase Order, Goods Received Note, and Invoice.

        Args:
            po: Purchase Order dataclass or dictionary.
            grn: Goods Received Note dataclass or dictionary.
            invoice: Supplier Invoice dataclass or dictionary.

        Returns:
            VerificationResult containing match status and structured discrepancies.
        """
        discrepancies: List[Discrepancy] = []

        po_dict = self._normalize_doc(po, "PurchaseOrder")
        grn_dict = self._normalize_doc(grn, "GoodsReceivedNote")
        inv_dict = self._normalize_doc(invoice, "SupplierInvoice")

        # 1. Validation & Extraction: Purchase Order
        po_num = self._validate_required_string(po_dict.get("po_number"), "po_number", "PO", discrepancies)
        po_sup = self._validate_required_string(po_dict.get("supplier_id"), "supplier_id", "PO", discrepancies)
        po_item = self._validate_required_string(po_dict.get("item_id"), "item_id", "PO", discrepancies)
        po_qty = self._to_decimal(po_dict.get("quantity"), "quantity", "PO", discrepancies)
        po_price = self._to_decimal(po_dict.get("unit_price"), "unit_price", "PO", discrepancies)
        po_curr = str(po_dict.get("currency", "USD")).strip().upper() if po_dict.get("currency") else "USD"

        # 2. Validation & Extraction: Goods Received Note
        grn_num = self._validate_required_string(grn_dict.get("grn_number"), "grn_number", "GRN", discrepancies)
        grn_po_ref = self._validate_required_string(
            grn_dict.get("po_number") or grn_dict.get("po_reference"), "po_number", "GRN", discrepancies
        )
        grn_sup = self._validate_required_string(grn_dict.get("supplier_id"), "supplier_id", "GRN", discrepancies)
        grn_item = self._validate_required_string(grn_dict.get("item_id"), "item_id", "GRN", discrepancies)
        grn_qty = self._to_decimal(grn_dict.get("quantity"), "quantity", "GRN", discrepancies)

        # 3. Validation & Extraction: Supplier Invoice
        inv_num = self._validate_required_string(inv_dict.get("invoice_number"), "invoice_number", "Invoice", discrepancies)
        inv_po_ref = self._validate_required_string(
            inv_dict.get("po_number") or inv_dict.get("po_reference"), "po_number", "Invoice", discrepancies
        )
        inv_sup = self._validate_required_string(inv_dict.get("supplier_id"), "supplier_id", "Invoice", discrepancies)
        inv_item = self._validate_required_string(inv_dict.get("item_id"), "item_id", "Invoice", discrepancies)
        inv_qty = self._to_decimal(inv_dict.get("quantity"), "quantity", "Invoice", discrepancies)
        inv_price = self._to_decimal(inv_dict.get("unit_price"), "unit_price", "Invoice", discrepancies)
        inv_curr = str(inv_dict.get("currency", "USD")).strip().upper() if inv_dict.get("currency") else "USD"

        # If fundamental identifiers are missing, return early with validation discrepancies
        if not (po_num and grn_po_ref and inv_po_ref and po_sup and grn_sup and inv_sup):
            return self._build_result(discrepancies, po_dict, grn_dict, inv_dict)

        # 4. Check Reference Agreement (PO Reference across GRN and Invoice)
        if grn_po_ref != po_num:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.REFERENCE_MISMATCH,
                field="grn.po_number",
                message=f"GRN PO reference '{grn_po_ref}' does not match PO number '{po_num}'. Marked for human review.",
                expected=po_num,
                actual=grn_po_ref,
            ))

        if inv_po_ref != po_num:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.REFERENCE_MISMATCH,
                field="invoice.po_number",
                message=f"Invoice PO reference '{inv_po_ref}' does not match PO number '{po_num}'. Marked for human review.",
                expected=po_num,
                actual=inv_po_ref,
            ))

        # 5. Check Supplier Consistency
        if grn_sup != po_sup:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.SUPPLIER_MISMATCH,
                field="grn.supplier_id",
                message=f"GRN supplier '{grn_sup}' does not match PO supplier '{po_sup}'. Marked for human review.",
                expected=po_sup,
                actual=grn_sup,
            ))

        if inv_sup != po_sup:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.SUPPLIER_MISMATCH,
                field="invoice.supplier_id",
                message=f"Invoice supplier '{inv_sup}' does not match PO supplier '{po_sup}'. Marked for human review.",
                expected=po_sup,
                actual=inv_sup,
            ))

        # 6. Check Item Identifier Agreement
        if po_item and grn_item and (grn_item != po_item):
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.ITEM_MISMATCH,
                field="grn.item_id",
                message=f"GRN item '{grn_item}' does not match PO item '{po_item}'. Marked for human review.",
                expected=po_item,
                actual=grn_item,
            ))

        if po_item and inv_item and (inv_item != po_item):
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.ITEM_MISMATCH,
                field="invoice.item_id",
                message=f"Invoice item '{inv_item}' does not match PO item '{po_item}'. Marked for human review.",
                expected=po_item,
                actual=inv_item,
            ))

        # 7. Quantity Comparison (Ordered vs Received vs Invoiced)
        if po_qty is not None and grn_qty is not None and inv_qty is not None:
            # Ordered vs Received
            if grn_qty < (po_qty - self.qty_tolerance):
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.QUANTITY_MISMATCH,
                    field="grn.quantity",
                    message=f"Received quantity ({grn_qty}) is less than ordered quantity ({po_qty}) (partial delivery). Marked for human review.",
                    expected=po_qty,
                    actual=grn_qty,
                ))
            elif grn_qty > (po_qty + self.qty_tolerance):
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.QUANTITY_MISMATCH,
                    field="grn.quantity",
                    message=f"Received quantity ({grn_qty}) exceeds ordered quantity ({po_qty}) (over-delivery). Marked for human review.",
                    expected=po_qty,
                    actual=grn_qty,
                ))

            # Invoiced vs Received (Core 3-Way match vulnerability: billing for unreceived goods)
            if inv_qty > (grn_qty + self.qty_tolerance):
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.QUANTITY_MISMATCH,
                    field="invoice.quantity",
                    message=f"Invoiced quantity ({inv_qty}) exceeds received quantity ({grn_qty}). Marked for human review.",
                    expected=grn_qty,
                    actual=inv_qty,
                ))
            elif inv_qty < (grn_qty - self.qty_tolerance):
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.QUANTITY_MISMATCH,
                    field="invoice.quantity",
                    message=f"Invoiced quantity ({inv_qty}) is less than received quantity ({grn_qty}) (partial billing). Marked for human review.",
                    expected=grn_qty,
                    actual=inv_qty,
                ))

            # Invoiced vs Ordered (billing exceeding original authorization)
            if inv_qty > (po_qty + self.qty_tolerance) and (grn_qty <= po_qty):
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.QUANTITY_MISMATCH,
                    field="invoice.quantity",
                    message=f"Invoiced quantity ({inv_qty}) exceeds PO ordered quantity ({po_qty}). Marked for human review.",
                    expected=po_qty,
                    actual=inv_qty,
                ))

        # 8. Unit Price Comparison (PO Unit Price vs Invoice Unit Price)
        if po_price is not None and inv_price is not None:
            price_diff = abs(inv_price - po_price)
            if price_diff > self.price_tolerance:
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.PRICE_MISMATCH,
                    field="invoice.unit_price",
                    message=f"Invoice unit price ({inv_price}) does not match PO agreed price ({po_price}) (variance: {inv_price - po_price:+}). Marked for human review.",
                    expected=po_price,
                    actual=inv_price,
                ))

        # 9. Currency Agreement
        if po_curr != inv_curr:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.CURRENCY_MISMATCH,
                field="invoice.currency",
                message=f"Invoice currency '{inv_curr}' does not match PO currency '{po_curr}'. Marked for human review.",
                expected=po_curr,
                actual=inv_curr,
            ))

        return self._build_result(discrepancies, po_dict, grn_dict, inv_dict)

    def _build_result(
        self,
        discrepancies: List[Discrepancy],
        po_dict: Dict[str, Any],
        grn_dict: Dict[str, Any],
        inv_dict: Dict[str, Any],
    ) -> VerificationResult:
        """Assemble structured result with summary."""
        is_match = (len(discrepancies) == 0)
        status = VerificationStatus.MATCHED if is_match else VerificationStatus.REQUIRES_HUMAN_REVIEW

        if is_match:
            summary = "Three-way match successful: PO, GRN, and Invoice are fully consistent."
        else:
            summary = (
                f"Verification completed with {len(discrepancies)} discrepancy(ies). "
                f"Action required: marked for human review."
            )

        doc_summary = {
            "po_number": po_dict.get("po_number"),
            "grn_number": grn_dict.get("grn_number"),
            "invoice_number": inv_dict.get("invoice_number"),
        }

        return VerificationResult(
            is_match=is_match,
            status=status,
            discrepancies=discrepancies,
            summary=summary,
            documents=doc_summary,
        )
