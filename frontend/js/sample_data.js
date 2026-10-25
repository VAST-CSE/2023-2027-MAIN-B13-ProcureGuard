/**
 * Benchmark procurement datasets and mock risk metrics.
 * 
 * NOTE FOR COLLEGE PROJECT / DEMO AUDIT:
 * - Procurement packages (PO, GRN, Invoice) are verified against the real VerificationEngine.
 * - Supplier Risk metrics are explicitly marked as DEMO / SAMPLE FIXTURES until the Phase 3 ML model.
 */

const SAMPLE_PROCUREMENT_PACKAGES = [
  {
    package_id: "PKG-2026-001",
    scenario_title: "Steel Beams Supply (Perfect 3-Way Match)",
    description: "Purchase order, delivery receipt, and vendor invoice agree perfectly.",
    po: {
      po_number: "PO-2026-001",
      supplier_id: "SUP-GLOBAL-88",
      supplier_name: "Global Steel Works Ltd",
      item_id: "SKU-BEAM-A1",
      item_name: "Reinforced Structural Steel Beam",
      quantity: 100,
      unit_price: 45.50,
      currency: "USD"
    },
    grn: {
      grn_number: "GRN-2026-089",
      po_number: "PO-2026-001",
      supplier_id: "SUP-GLOBAL-88",
      item_id: "SKU-BEAM-A1",
      quantity: 100
    },
    invoice: {
      invoice_number: "INV-2026-4501",
      po_number: "PO-2026-001",
      supplier_id: "SUP-GLOBAL-88",
      item_id: "SKU-BEAM-A1",
      quantity: 100,
      unit_price: 45.50,
      currency: "USD"
    }
  },
  {
    package_id: "PKG-2026-002",
    scenario_title: "Industrial Valves (Invoiced Quantity Exceeds Received)",
    description: "Vendor billed for 120 units, but warehouse only received and logged 100 units.",
    po: {
      po_number: "PO-2026-002",
      supplier_id: "SUP-APEX-14",
      supplier_name: "Apex Fluid Dynamics",
      item_id: "SKU-VALVE-V2",
      item_name: "High-Pressure Hydraulic Valve",
      quantity: 100,
      unit_price: 180.00,
      currency: "USD"
    },
    grn: {
      grn_number: "GRN-2026-092",
      po_number: "PO-2026-002",
      supplier_id: "SUP-APEX-14",
      item_id: "SKU-VALVE-V2",
      quantity: 100
    },
    invoice: {
      invoice_number: "INV-2026-4502",
      po_number: "PO-2026-002",
      supplier_id: "SUP-APEX-14",
      item_id: "SKU-VALVE-V2",
      quantity: 120, // Discrepancy: +20 unreceived units
      unit_price: 180.00,
      currency: "USD"
    }
  },
  {
    package_id: "PKG-2026-003",
    scenario_title: "Microcontrollers (Unit Price Deviation)",
    description: "Invoice unit price ($52.00) differs from contracted PO unit price ($45.00).",
    po: {
      po_number: "PO-2026-003",
      supplier_id: "SUP-NEXUS-09",
      supplier_name: "Nexus Electronics Corp",
      item_id: "SKU-MCU-X86",
      item_name: "Industrial Core Microcontroller",
      quantity: 500,
      unit_price: 45.00,
      currency: "USD"
    },
    grn: {
      grn_number: "GRN-2026-098",
      po_number: "PO-2026-003",
      supplier_id: "SUP-NEXUS-09",
      item_id: "SKU-MCU-X86",
      quantity: 500
    },
    invoice: {
      invoice_number: "INV-2026-4503",
      po_number: "PO-2026-003",
      supplier_id: "SUP-NEXUS-09",
      item_id: "SKU-MCU-X86",
      quantity: 500,
      unit_price: 52.00, // Discrepancy: +$7.00 per unit price surge
      currency: "USD"
    }
  },
  {
    package_id: "PKG-2026-004",
    scenario_title: "Copper Cables (PO Reference & Vendor Mismatch)",
    description: "Goods receipt note cites an unknown PO reference and unmatched supplier code.",
    po: {
      po_number: "PO-2026-004",
      supplier_id: "SUP-METALS-55",
      supplier_name: "Metals & Wiring Logistics",
      item_id: "SKU-CAB-C4",
      item_name: "High-Conductivity Copper Cable 50m",
      quantity: 80,
      unit_price: 95.00,
      currency: "USD"
    },
    grn: {
      grn_number: "GRN-2026-104",
      po_number: "PO-WRONG-REF-99", // Reference mismatch
      supplier_id: "SUP-UNKNOWN-VENDOR", // Supplier mismatch
      item_id: "SKU-CAB-C4",
      quantity: 80
    },
    invoice: {
      invoice_number: "INV-2026-4504",
      po_number: "PO-2026-004",
      supplier_id: "SUP-METALS-55",
      item_id: "SKU-CAB-C4",
      quantity: 80,
      unit_price: 95.00,
      currency: "USD"
    }
  },
  {
    package_id: "PKG-2026-005",
    scenario_title: "Heavy Lubricants (Missing Mandatory Values)",
    description: "Purchase order is missing required unit price and quantity.",
    po: {
      po_number: "PO-2026-005",
      supplier_id: "SUP-LUBE-21",
      supplier_name: "AeroLube Synthetic Oils",
      item_id: "SKU-OIL-SYN",
      item_name: "Synthetic High-Temp Gear Lubricant",
      quantity: "", // Missing quantity
      unit_price: null, // Missing unit price
      currency: "USD"
    },
    grn: {
      grn_number: "GRN-2026-110",
      po_number: "PO-2026-005",
      supplier_id: "SUP-LUBE-21",
      item_id: "SKU-OIL-SYN",
      quantity: 40
    },
    invoice: {
      invoice_number: "INV-2026-4505",
      po_number: "PO-2026-005",
      supplier_id: "SUP-LUBE-21",
      item_id: "SKU-OIL-SYN",
      quantity: 40,
      unit_price: 110.00,
      currency: "USD"
    }
  }
];

/**
 * DEMO / SAMPLE SUPPLIER RISK PROFILES
 * Explicitly designated as mock indicators for demonstration purposes.
 * Real predictive modeling is scheduled for Phase 3.
 */
const SAMPLE_SUPPLIERS_RISK_DATA = [
  {
    supplier_id: "SUP-GLOBAL-88",
    supplier_name: "Global Steel Works Ltd",
    category: "Raw Metals & Construction",
    sample_risk_score: 18,
    sample_risk_tier: "LOW",
    metrics: {
      on_time_delivery_rate: "98.4%",
      invoice_accuracy_rate: "99.1%",
      average_lead_time_days: 12,
      variance_history_count: 1
    },
    demo_notes: "Sample indicator: Consistent delivery track record and reliable pricing agreement compliance."
  },
  {
    supplier_id: "SUP-APEX-14",
    supplier_name: "Apex Fluid Dynamics",
    category: "Mechanical & Hydraulics",
    sample_risk_score: 54,
    sample_risk_tier: "MEDIUM",
    metrics: {
      on_time_delivery_rate: "89.2%",
      invoice_accuracy_rate: "87.5%",
      average_lead_time_days: 24,
      variance_history_count: 4
    },
    demo_notes: "Sample indicator: Recurring quantity billing discrepancies between warehouse GRN and supplier invoices."
  },
  {
    supplier_id: "SUP-NEXUS-09",
    supplier_name: "Nexus Electronics Corp",
    category: "Semiconductors & Components",
    sample_risk_score: 76,
    sample_risk_tier: "HIGH",
    metrics: {
      on_time_delivery_rate: "78.0%",
      invoice_accuracy_rate: "81.2%",
      average_lead_time_days: 45,
      variance_history_count: 7
    },
    demo_notes: "Sample indicator: Supply chain chip shortage volatility and unit-price fluctuations above contracted rates."
  },
  {
    supplier_id: "SUP-METALS-55",
    supplier_name: "Metals & Wiring Logistics",
    category: "Electrical Conductors",
    sample_risk_score: 42,
    sample_risk_tier: "MEDIUM",
    metrics: {
      on_time_delivery_rate: "91.5%",
      invoice_accuracy_rate: "92.0%",
      average_lead_time_days: 18,
      variance_history_count: 3
    },
    demo_notes: "Sample indicator: Moderate lead-time variations with occasional PO reference formatting differences."
  }
];

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SAMPLE_PROCUREMENT_PACKAGES,
    SAMPLE_SUPPLIERS_RISK_DATA
  };
}
