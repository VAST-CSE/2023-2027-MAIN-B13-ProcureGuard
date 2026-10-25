/**
 * API connector for Intelligent Procurement System.
 * 
 * Interacts with the Python VerificationEngine backend (/api/verify).
 * Supports graceful client fallback if opened directly from local disk (file://).
 */

const ApiService = {
  isBackendConnected: false,

  /**
   * Check if the Python backend is active.
   */
  async checkHealth() {
    try {
      const res = await fetch("/api/health", { method: "GET" });
      if (res.ok) {
        this.isBackendConnected = true;
        return true;
      }
    } catch (e) {
      this.isBackendConnected = false;
    }
    return false;
  },

  /**
   * Run 3-way match verification on a procurement package.
   * Calls the actual Python VerificationEngine backend when available.
   */
  async verifyPackage(pkg) {
    if (window.location.protocol.startsWith("http")) {
      try {
        const response = await fetch("/api/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            po: pkg.po,
            grn: pkg.grn,
            invoice: pkg.invoice
          })
        });

        if (response.ok) {
          const data = await response.json();
          this.isBackendConnected = true;
          return {
            ...data,
            package_id: pkg.package_id,
            scenario_title: pkg.scenario_title,
            source: "Python Live Engine (app/verification/engine.py)"
          };
        }
      } catch (err) {
        console.warn("Backend /api/verify not reachable. Using standard client rules.", err);
      }
    }

    // Graceful offline fallback mirroring VerificationEngine logic
    return this.clientFallbackVerify(pkg);
  },

  /**
   * Client-side rules engine fallback (preserves identical logic to VerificationEngine).
   * Ensures the student demo functions seamlessly even if opened via file://.
   */
  clientFallbackVerify(pkg) {
    const { po, grn, invoice } = pkg;
    const discrepancies = [];

    // 1. Data validation checks
    const checkRequired = (val, fieldName, docName) => {
      if (val === undefined || val === null || String(val).trim() === "") {
        discrepancies.push({
          type: "DATA_VALIDATION_ERROR",
          field: `${docName}.${fieldName}`,
          message: `Missing required value for '${fieldName}' in ${docName}. Marked for human review.`,
          expected: "valid value",
          actual: val,
          requires_human_review: true
        });
        return false;
      }
      return true;
    };

    const poNumValid = checkRequired(po.po_number, "po_number", "PO");
    const grnPoValid = checkRequired(grn.po_number, "po_number", "GRN");
    const invPoValid = checkRequired(invoice.po_number, "po_number", "Invoice");
    const poQtyValid = checkRequired(po.quantity, "quantity", "PO");
    const poPriceValid = checkRequired(po.unit_price, "unit_price", "PO");

    if (poNumValid && grnPoValid && invPoValid && poQtyValid && poPriceValid) {
      // 2. Reference checks
      if (grn.po_number !== po.po_number) {
        discrepancies.push({
          type: "REFERENCE_MISMATCH",
          field: "grn.po_number",
          message: `GRN PO reference '${grn.po_number}' does not match PO number '${po.po_number}'. Marked for human review.`,
          expected: po.po_number,
          actual: grn.po_number,
          requires_human_review: true
        });
      }

      if (invoice.po_number !== po.po_number) {
        discrepancies.push({
          type: "REFERENCE_MISMATCH",
          field: "invoice.po_number",
          message: `Invoice PO reference '${invoice.po_number}' does not match PO number '${po.po_number}'. Marked for human review.`,
          expected: po.po_number,
          actual: invoice.po_number,
          requires_human_review: true
        });
      }

      // 3. Supplier checks
      if (grn.supplier_id !== po.supplier_id) {
        discrepancies.push({
          type: "SUPPLIER_MISMATCH",
          field: "grn.supplier_id",
          message: `GRN supplier '${grn.supplier_id}' does not match PO supplier '${po.supplier_id}'. Marked for human review.`,
          expected: po.supplier_id,
          actual: grn.supplier_id,
          requires_human_review: true
        });
      }

      // 4. Quantity comparisons
      const poQty = Number(po.quantity);
      const grnQty = Number(grn.quantity);
      const invQty = Number(invoice.quantity);

      if (invQty > grnQty) {
        discrepancies.push({
          type: "QUANTITY_MISMATCH",
          field: "invoice.quantity",
          message: `Invoiced quantity (${invQty}) exceeds received quantity (${grnQty}). Marked for human review.`,
          expected: grnQty,
          actual: invQty,
          requires_human_review: true
        });
      }

      // 5. Unit price checks
      const poPrice = Number(po.unit_price);
      const invPrice = Number(invoice.unit_price);
      if (poPrice !== invPrice) {
        discrepancies.push({
          type: "PRICE_MISMATCH",
          field: "invoice.unit_price",
          message: `Invoice unit price (${invPrice}) does not match PO agreed price (${poPrice}). Marked for human review.`,
          expected: poPrice,
          actual: invPrice,
          requires_human_review: true
        });
      }
    }

    const isMatch = discrepancies.length === 0;
    return {
      is_match: isMatch,
      status: isMatch ? "MATCHED" : "REQUIRES_HUMAN_REVIEW",
      discrepancy_count: discrepancies.length,
      discrepancies: discrepancies,
      summary: isMatch
        ? "Three-way match successful: PO, GRN, and Invoice are fully consistent."
        : `Verification completed with ${discrepancies.length} discrepancy(ies). Action required: marked for human review.`,
      package_id: pkg.package_id,
      scenario_title: pkg.scenario_title,
      source: "Client Fallback Mode (Offline)"
    };
  }
};
