/**
 * Main Frontend Application Controller for Intelligent Procurement System.
 */

document.addEventListener("DOMContentLoaded", () => {
  AppState.init();
});

const AppState = {
  activeTab: "dashboard",
  verificationResults: [],
  reviewedDiscrepancies: new Set(),
  activeFilter: "ALL",

  async init() {
    this.bindNavigation();
    this.bindActions();
    await this.runVerificationBatch();
    this.renderTransactions();
    this.renderSupplierRisk();
    await this.updateBackendIndicator();
  },

  async updateBackendIndicator() {
    const isLive = await ApiService.checkHealth();
    const indicatorEl = document.getElementById("backend-status-pill");
    if (indicatorEl) {
      if (isLive) {
        indicatorEl.innerHTML = `<span class="engine-pulse"></span> Python Engine: Active (/api/verify)`;
        indicatorEl.title = "Connected to Python stdlib server using app/verification/engine.py";
      } else {
        indicatorEl.innerHTML = `<span style="width:6px;height:6px;border-radius:50%;background:#FBBF24;display:inline-block;"></span> Client Engine: Standalone`;
        indicatorEl.title = "Operating in client standalone mode. Run 'python app/server.py' for Python API.";
      }
    }
  },

  bindNavigation() {
    const links = document.querySelectorAll(".nav-link[data-tab]");
    links.forEach(link => {
      link.addEventListener("click", e => {
        e.preventDefault();
        const tab = link.getAttribute("data-tab");
        this.switchTab(tab);
      });
    });
  },

  switchTab(tabName) {
    this.activeTab = tabName;

    // Update nav links
    document.querySelectorAll(".nav-link").forEach(link => {
      if (link.getAttribute("data-tab") === tabName) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Update tab panes
    document.querySelectorAll(".tab-pane").forEach(pane => {
      if (pane.id === `tab-${tabName}`) {
        pane.classList.add("active");
      } else {
        pane.classList.remove("active");
      }
    });

    // Refresh view specific components
    if (tabName === "discrepancies") {
      this.renderDiscrepancies();
    } else if (tabName === "transactions") {
      this.renderTransactions();
    }
  },

  bindActions() {
    const runBtn = document.getElementById("btn-run-all-verify");
    if (runBtn) {
      runBtn.addEventListener("click", () => {
        this.runVerificationBatch(true);
      });
    }

    const filterSelect = document.getElementById("discrepancy-filter");
    if (filterSelect) {
      filterSelect.addEventListener("change", (e) => {
        this.activeFilter = e.target.value;
        this.renderDiscrepancies();
      });
    }
  },

  async runVerificationBatch(showToast = false) {
    this.verificationResults = [];

    for (const pkg of SAMPLE_PROCUREMENT_PACKAGES) {
      const res = await ApiService.verifyPackage(pkg);
      this.verificationResults.push(res);
    }

    this.updateDashboardMetrics();
    this.renderRecentAuditFeed();
    this.renderDiscrepancies();

    if (showToast) {
      this.showToast(`Verified ${this.verificationResults.length} procurement packages successfully!`);
    }
  },

  updateDashboardMetrics() {
    const totalCount = this.verificationResults.length;
    const matchedCount = this.verificationResults.filter(r => r.is_match).length;
    const reviewCount = this.verificationResults.filter(r => !r.is_match).length;

    // Demo risk average
    const avgRisk = Math.round(
      SAMPLE_SUPPLIERS_RISK_DATA.reduce((acc, curr) => acc + curr.sample_risk_score, 0) /
      SAMPLE_SUPPLIERS_RISK_DATA.length
    );

    document.getElementById("kpi-total-tx").textContent = totalCount;
    document.getElementById("kpi-matched-tx").textContent = matchedCount;
    document.getElementById("kpi-review-tx").textContent = reviewCount;
    document.getElementById("kpi-demo-risk").textContent = `${avgRisk} / 100`;
  },

  renderRecentAuditFeed() {
    const tbody = document.getElementById("dashboard-audit-tbody");
    if (!tbody) return;

    tbody.innerHTML = this.verificationResults.map(res => {
      const badgeClass = res.is_match ? "badge-matched" : "badge-review";
      const statusLabel = res.is_match ? "3-WAY MATCHED" : "REQUIRES HUMAN REVIEW";
      const discCount = res.discrepancies ? res.discrepancies.length : 0;

      return `
        <tr>
          <td><span class="code-font">${res.package_id}</span></td>
          <td><strong>${res.scenario_title}</strong></td>
          <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
          <td>${discCount > 0 ? `${discCount} variance(s)` : '<span style="color:#34D399;">None (0)</span>'}</td>
          <td><span style="font-size:0.8rem; color:var(--text-muted);">${res.source || "Python Engine"}</span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="AppState.viewPackageDetails('${res.package_id}')">
              View
            </button>
          </td>
        </tr>
      `;
    }).join("");
  },

  renderTransactions() {
    const container = document.getElementById("transactions-list-container");
    if (!container) return;

    container.innerHTML = SAMPLE_PROCUREMENT_PACKAGES.map(pkg => {
      const result = this.verificationResults.find(r => r.package_id === pkg.package_id);
      const isMatch = result ? result.is_match : false;
      const statusBadge = isMatch
        ? `<span class="badge badge-matched">MATCHED</span>`
        : `<span class="badge badge-review">REQUIRES HUMAN REVIEW</span>`;

      return `
        <div class="match-package-card">
          <div class="match-package-header">
            <div class="package-id">
              <span class="code-font">${pkg.package_id}</span> — ${pkg.scenario_title}
            </div>
            <div>${statusBadge}</div>
          </div>
          <p style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:14px;">${pkg.description}</p>
          
          <div class="doc-triad-grid">
            <!-- 1. Purchase Order Tile -->
            <div class="doc-tile">
              <div class="doc-tile-title">📄 Purchase Order (PO)</div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">PO Number:</span>
                <span class="doc-detail-value code-font">${pkg.po.po_number || "<em>(Missing)</em>"}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Supplier ID:</span>
                <span class="doc-detail-value code-font">${pkg.po.supplier_id}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Item SKU:</span>
                <span class="doc-detail-value code-font">${pkg.po.item_id}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Ordered Qty:</span>
                <span class="doc-detail-value">${pkg.po.quantity ?? "<em>(Missing)</em>"}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Contract Price:</span>
                <span class="doc-detail-value">${pkg.po.unit_price ? `$${Number(pkg.po.unit_price).toFixed(2)}` : "<em>(Missing)</em>"}</span>
              </div>
            </div>

            <!-- 2. Goods Received Note Tile -->
            <div class="doc-tile">
              <div class="doc-tile-title">📦 Goods Received Note (GRN)</div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">GRN Number:</span>
                <span class="doc-detail-value code-font">${pkg.grn.grn_number}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Cited PO Ref:</span>
                <span class="doc-detail-value code-font">${pkg.grn.po_number}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Supplier ID:</span>
                <span class="doc-detail-value code-font">${pkg.grn.supplier_id}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Item SKU:</span>
                <span class="doc-detail-value code-font">${pkg.grn.item_id}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Received Qty:</span>
                <span class="doc-detail-value" style="color:#60A5FA;">${pkg.grn.quantity}</span>
              </div>
            </div>

            <!-- 3. Supplier Invoice Tile -->
            <div class="doc-tile">
              <div class="doc-tile-title">💳 Supplier Invoice</div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Invoice Number:</span>
                <span class="doc-detail-value code-font">${pkg.invoice.invoice_number}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Cited PO Ref:</span>
                <span class="doc-detail-value code-font">${pkg.invoice.po_number}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Supplier ID:</span>
                <span class="doc-detail-value code-font">${pkg.invoice.supplier_id}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Invoiced Qty:</span>
                <span class="doc-detail-value" style="color:#FBBF24;">${pkg.invoice.quantity}</span>
              </div>
              <div class="doc-detail-row">
                <span class="doc-detail-label">Billed Price:</span>
                <span class="doc-detail-value">${pkg.invoice.unit_price ? `$${Number(pkg.invoice.unit_price).toFixed(2)}` : "<em>(Missing)</em>"}</span>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join("");
  },

  renderDiscrepancies() {
    const tbody = document.getElementById("discrepancies-tbody");
    if (!tbody) return;

    let rows = [];

    this.verificationResults.forEach(res => {
      if (res.discrepancies && res.discrepancies.length > 0) {
        res.discrepancies.forEach((disc, idx) => {
          const discId = `${res.package_id}-${idx}`;
          const isReviewed = this.reviewedDiscrepancies.has(discId);

          if (this.activeFilter !== "ALL" && disc.type !== this.activeFilter) {
            return;
          }

          rows.push({
            id: discId,
            package_id: res.package_id,
            scenario: res.scenario_title,
            type: disc.type,
            field: disc.field,
            message: disc.message,
            expected: disc.expected,
            actual: disc.actual,
            isReviewed: isReviewed
          });
        });
      }
    });

    if (rows.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted);">
            No discrepancies match the selected filter.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = rows.map(r => `
      <tr style="${r.isReviewed ? 'opacity: 0.55;' : ''}">
        <td><span class="code-font">${r.package_id}</span></td>
        <td><span class="badge badge-review">${r.type}</span></td>
        <td><span class="code-font">${r.field}</span></td>
        <td>
          <div style="font-size:0.86rem;">${r.message}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
            Expected: <strong>${r.expected}</strong> | Actual: <strong>${r.actual}</strong>
          </div>
        </td>
        <td>
          ${r.isReviewed 
            ? `<span class="badge badge-matched">REVIEWED BY OFFICER</span>`
            : `<span class="badge badge-review">REQUIRES HUMAN REVIEW</span>`
          }
        </td>
        <td>
          <button 
            class="btn btn-secondary btn-sm" 
            onclick="AppState.toggleReviewDiscrepancy('${r.id}')"
          >
            ${r.isReviewed ? "Undo Review" : "Mark Reviewed"}
          </button>
        </td>
      </tr>
    `).join("");
  },

  toggleReviewDiscrepancy(discId) {
    if (this.reviewedDiscrepancies.has(discId)) {
      this.reviewedDiscrepancies.delete(discId);
      this.showToast("Discrepancy marked pending human review.");
    } else {
      this.reviewedDiscrepancies.add(discId);
      this.showToast("Variance marked as verified and noted by reviewer.");
    }
    this.renderDiscrepancies();
  },

  renderSupplierRisk() {
    const tbody = document.getElementById("supplier-risk-tbody");
    if (!tbody) return;

    tbody.innerHTML = SAMPLE_SUPPLIERS_RISK_DATA.map(sup => {
      let tierBadge = "";
      if (sup.sample_risk_tier === "LOW") {
        tierBadge = `<span class="badge badge-risk-low">LOW (${sup.sample_risk_score}/100)</span>`;
      } else if (sup.sample_risk_tier === "MEDIUM") {
        tierBadge = `<span class="badge badge-risk-medium">MEDIUM (${sup.sample_risk_score}/100)</span>`;
      } else {
        tierBadge = `<span class="badge badge-risk-high">HIGH (${sup.sample_risk_score}/100)</span>`;
      }

      return `
        <tr>
          <td>
            <div style="font-weight:700;">${sup.supplier_name}</div>
            <div class="code-font" style="font-size:0.76rem;">${sup.supplier_id}</div>
          </td>
          <td>${sup.category}</td>
          <td>${tierBadge}</td>
          <td>${sup.metrics.on_time_delivery_rate}</td>
          <td>${sup.metrics.invoice_accuracy_rate}</td>
          <td>${sup.metrics.average_lead_time_days} days</td>
          <td>
            <div style="font-size:0.8rem; color:var(--text-secondary); max-width:280px;">
              ${sup.demo_notes}
            </div>
            <div style="font-size:0.72rem; color:var(--status-demo-text); margin-top:2px;">
              * Demo mock indicator
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  viewPackageDetails(packageId) {
    this.switchTab("transactions");
    setTimeout(() => {
      const cards = document.querySelectorAll(".match-package-card");
      cards.forEach(card => {
        if (card.textContent.includes(packageId)) {
          card.scrollIntoView({ behavior: "smooth", block: "center" });
          card.style.borderColor = "#6366F1";
          setTimeout(() => { card.style.borderColor = ""; }, 2000);
        }
      });
    }, 100);
  },

  showToast(message) {
    const existing = document.querySelector(".toast-box");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "toast-box";
    toast.innerHTML = `<span>⚡</span> <div>${message}</div>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }
};
