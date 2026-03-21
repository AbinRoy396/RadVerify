(() => {
  const state = {
    role: "Radiologist",
    user: { name: "RAVEN Operator", title: "Clinical Reviewer" },
    page: "upload",
    scanFile: null,
    scanPreview: "",
    reportText: "",
    result: null,
    exportConfig: { heatmap: true, summary: true, narrative: true, discrepancy: true },
    resolution: {},
    history: [
      {
        id: "SCN-9021",
        type: "Chest PA/Lateral X-Ray",
        patient: "PAT-7728-B",
        timestamp: "Oct 24, 10:45 AM",
        status: "verified",
      },
      {
        id: "SCN-8842",
        type: "Abdominal Ultrasound",
        patient: "PAT-9102-X",
        timestamp: "Oct 24, 09:12 AM",
        status: "discrepancy",
      },
      {
        id: "SCN-8811",
        type: "Lumbar Spine MRI",
        patient: "PAT-1142-D",
        timestamp: "Oct 23, 04:55 PM",
        status: "processing",
      },
    ],
  };

  const NAV = [
    { key: "upload", label: "Dashboard", icon: "dashboard", sub: "Clinical input and processing" },
    { key: "analysis", label: "Analysis Workspace", icon: "biotech", sub: "AI findings and report comparison" },
    { key: "discrepancy", label: "Discrepancy Resolution", icon: "rule_settings", sub: "Resolve mismatches and omissions" },
    { key: "export", label: "Final Export", icon: "picture_as_pdf", sub: "Finalize and archive output" },
    { key: "history", label: "History & Archive", icon: "history", sub: "Compliance-grade retrieval" },
    { key: "help", label: "Help Center", icon: "help_center", sub: "Docs and guidance" },
  ];

  const $ = (id) => document.getElementById(id);

  function getSidebar() {
    return document.querySelector(".sidebar");
  }

  function isMobile() {
    return window.matchMedia("(max-width: 980px)").matches;
  }

  function ensureSidebarBackdrop() {
    let el = $("sidebarBackdrop");
    if (el) return el;

    el = document.createElement("div");
    el.id = "sidebarBackdrop";
    el.className = "backdrop";
    el.hidden = true;
    document.body.appendChild(el);
    return el;
  }

  function showSidebar(open) {
    const sb = getSidebar();
    if (!sb) return;

    sb.setAttribute("data-open", String(Boolean(open)));

    const bd = ensureSidebarBackdrop();
    if (isMobile()) {
      show(bd, Boolean(open));
    } else {
      show(bd, false);
    }
  }

  function esc(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function show(el, v) {
    if (!el) return;
    el.hidden = !v;
  }

  function openModal({ title, bodyHTML, footerHTML }) {
    $("modalTitle").textContent = title || "";
    $("modalBody").innerHTML = bodyHTML || "";
    $("modalFooter").innerHTML = footerHTML || "";

    // Modal overlay only (do not reuse for sidebar)
    showSidebar(false);
    show($("backdrop"), true);
    show($("modal"), true);
  }

  function closeModal() {
    show($("backdrop"), false);
    show($("modal"), false);
  }

  // Reusable UI components (HTML factories)
  function uiIcon(name) {
    return `<span class="material-symbols-outlined" aria-hidden="true">${esc(name)}</span>`;
  }

  function uiButton({ label, variant = "default", icon, id, disabled = false, extraClass = "" }) {
    const cls =
      variant === "primary"
        ? "btn btn--primary"
        : variant === "danger"
          ? "btn btn--danger"
          : variant === "ghost"
            ? "btn btn--ghost"
            : "btn";

    return `
      <button ${id ? `id="${esc(id)}"` : ""} class="${cls} ${extraClass}" type="button" ${disabled ? "disabled" : ""}>
        ${icon ? uiIcon(icon) : ""}
        ${esc(label)}
      </button>
    `;
  }

  function uiCard({ headerHTML = "", bodyHTML = "" }) {
    return `
      <div class="card">
        ${headerHTML ? `<div class="card__header">${headerHTML}</div>` : ""}
        <div class="card__body">${bodyHTML}</div>
      </div>
    `;
  }

  function uiBadge(status) {
    const s = String(status || "").toLowerCase();
    if (s === "verified") {
      return `<span class="badge badge--ok"><span class="badge__dot"></span>Verified</span>`;
    }
    if (s === "discrepancy") {
      return `<span class="badge badge--bad"><span class="badge__dot"></span>Discrepancy Found</span>`;
    }
    if (s === "processing") {
      return `<span class="badge badge--warn"><span class="badge__dot"></span>Processing</span>`;
    }
    return `<span class="badge"><span class="badge__dot"></span>${esc(status || "-")}</span>`;
  }

  function setStatusPill(kind) {
    const pill = $("statusPill");
    if (!pill) return;

    if (!kind) {
      pill.hidden = true;
      pill.className = "pill";
      pill.textContent = "";
      return;
    }

    pill.hidden = false;
    pill.className = "pill";

    if (kind === "bad") {
      pill.classList.add("pill--bad");
      pill.textContent = "Discrepancy";
      return;
    }
    if (kind === "warn") {
      pill.classList.add("pill--warn");
      pill.textContent = "Review Needed";
      return;
    }
    pill.classList.add("pill--ok");
    pill.textContent = "Match";
  }

  function renderNav() {
    const nav = $("nav");
    nav.innerHTML = NAV.map((n) => {
      const current = n.key === state.page;
      return `
        <button class="nav-item" id="nav-${esc(n.key)}" type="button" ${current ? 'aria-current="page"' : ""}>
          <span class="nav-item__icon">${uiIcon(n.icon)}</span>
          <span>${esc(n.label)}</span>
        </button>
      `;
    }).join("");

    NAV.forEach((n) => {
      const el = $("nav-" + n.key);
      el?.addEventListener("click", () => {
        if (["analysis", "discrepancy", "export"].includes(n.key) && !state.result) {
          openModal({
            title: "Demo Navigation",
            bodyHTML: `<p class="small">Run a demo analysis first from <b>Dashboard</b> to populate this screen.</p>`,
            footerHTML: uiButton({ label: "Got it", variant: "primary", id: "modalOk" }),
          });
          $("modalOk")?.addEventListener("click", closeModal);
          return;
        }
        setPage(n.key);
      });
    });
  }

  function setPage(pageKey) {
    state.page = pageKey;
    renderNav();

    const meta = NAV.find((n) => n.key === pageKey);
    $("pageTitle").textContent = meta?.label || "";
    $("pageSub").textContent = meta?.sub || "";

    if (pageKey === "upload") renderUpload();
    else if (pageKey === "analysis") renderAnalysis();
    else if (pageKey === "discrepancy") renderDiscrepancy();
    else if (pageKey === "export") renderExport();
    else if (pageKey === "history") renderHistory();
    else renderHelp();
  }

  function mockRunAnalysis() {
    state.result = {
      agreement: 0.78,
      risk: "HIGH",
      study: "DOE, JOHN | 45Y | Chest X-Ray (PA View)",
      studyId: "88291-XA",
      timestamp: "OCT 24, 2023 09:42 AM",
      findings: [
        {
          name: "Cardiomegaly",
          confidence: 0.98,
          rationale:
            "Transverse heart diameter exceeds 50% of thoracic diameter. Likely indicative of underlying CHF.",
          severity: "active",
        },
        {
          name: "Pleural Effusion",
          confidence: 0.82,
          rationale: "Blunting of the right costophrenic angle suggesting mild fluid accumulation.",
          severity: "neutral",
        },
        {
          name: "Pulmonary Nodule",
          confidence: 0.22,
          rationale: "Shadow in upper left lobe; likely vessel end-on or artifact.",
          severity: "low",
        },
      ],
      reportHTML: `
        <p>
          Lungs are clear bilaterally without focal consolidation.
          <span class="hl-bad" title="AI detected Cardiomegaly (98% confidence)">The cardiomediastinal silhouette is within normal limits.</span>
          The pulmonary vasculature is not congested.
        </p>
        <p>
          No evidence of pneumothorax is seen.
          <span class="hl-warn" title="Potential Omission: AI detected mild blunting of right costophrenic angle">Bony structures and soft tissues are unremarkable.</span>
        </p>
        <p style="opacity:0.75; font-style: italic;">
          IMPRESSION: No acute cardiopulmonary abnormality.
        </p>
      `,
      discrepancyText:
        "The human report indicates a \"normal\" heart size, but Stitch Analysis detects a cardiothoracic ratio of 0.58, which constitutes cardiomegaly.",
      queue: [
        { key: "Cardiomegaly", category: "Cardiac", status: "mismatch" },
        { key: "Pleural Effusion", category: "Pleura", status: "omission" },
      ],
    };

    setStatusPill("bad");
  }

  function renderUpload() {
    setStatusPill(state.result ? "bad" : null);

    const view = $("view");
    view.innerHTML = `
      <div style="max-width:720px;">
        <h1 class="h1 hero-title">Verify New Medical Scans</h1>
        <div class="hero-sub">Pair medical imagery with human-written reports for high-precision cross-validation.</div>
      </div>

      <div class="grid grid--2" style="margin-top: 18px;">
        <div class="field">
          <div class="label">${uiIcon("image")} 1. Upload Medical Scans</div>
          <label class="dropzone" for="scanInput">
            <div class="dropzone__icon">${uiIcon("upload_file")}</div>
            <div class="dropzone__title">Drag & drop files here</div>
            <div class="dropzone__sub">Support for DICOM, JPEG, PNG (demo only)</div>
            <div class="dropzone__chips">
              <span class="chip">DICOM</span>
              <span class="chip">JPEG</span>
              <span class="chip">PNG</span>
              <span class="chip">TIFF</span>
            </div>
            <div id="scanName" class="small" style="margin-top: 12px;"></div>
          </label>
          <input id="scanInput" type="file" accept="image/*" hidden />
        </div>

        <div class="field">
          <div class="label">${uiIcon("subject")} 2. Human-Written Radiology Report</div>
          <textarea id="reportInput" class="textarea" placeholder="Paste the official radiology report text here. Be sure to include patient ID and clinical indications..."></textarea>
        </div>
      </div>

      <div class="action-bar" style="margin-top: 16px;">
        <div class="action-bar__left">${uiIcon("info")}<p>Ensure all patient identifiers are redacted if required by local policy.</p></div>
        ${uiButton({ label: "Start Demo Analysis", variant: "primary", icon: "bolt", id: "startBtn", disabled: true })}
      </div>

      <div style="margin-top: 20px; display:flex; align-items:center; justify-content:space-between; gap: 10px;">
        <div style="font-size: 18px; font-weight: 900;">Recent Activity</div>
        ${uiButton({ label: "View Full History", variant: "ghost", id: "goHistory" })}
      </div>

      ${uiCard({
        bodyHTML: `
          <div class="table-wrap">
            <table class="table" aria-label="Recent activity">
              <thead>
                <tr>
                  <th>Scan ID / Type</th>
                  <th>Patient Ref</th>
                  <th>Timestamp</th>
                  <th>Verification Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${state.history
                  .slice(0, 3)
                  .map((r) => {
                    const action = r.status === "discrepancy" ? "Review" : r.status === "processing" ? "Waiting" : "Open";
                    return `
                      <tr>
                        <td>
                          <div style="display:flex; gap: 12px; align-items:center;">
                            <div style="width:40px; height:40px; border-radius: 12px; display:flex; align-items:center; justify-content:center; background:#f0f2f4; color: var(--primary);">${uiIcon(
                              "radiology"
                            )}</div>
                            <div>
                              <div style="font-weight: 900;">#${esc(r.id)}</div>
                              <div class="small">${esc(r.type)}</div>
                            </div>
                          </div>
                        </td>
                        <td style="font-weight:700;">${esc(r.patient)}</td>
                        <td style="color: var(--muted);">${esc(r.timestamp)}</td>
                        <td>${uiBadge(r.status)}</td>
                        <td>${uiButton({ label: action, variant: "ghost", id: `act-${esc(r.id)}` })}</td>
                      </tr>
                    `;
                  })
                  .join("")}
              </tbody>
            </table>
          </div>
        `,
      })}
    `;

    const scanInput = $("scanInput");
    const reportInput = $("reportInput");
    const startBtn = $("startBtn");

    function syncStartEnabled() {
      state.reportText = reportInput.value;
      startBtn.disabled = !(state.scanFile && state.reportText.trim());
    }

    scanInput.addEventListener("change", (e) => {
      state.scanFile = e.target.files?.[0] || null;
      $("scanName").textContent = state.scanFile ? `Selected: ${state.scanFile.name}` : "";

      if (state.scanFile) {
        const fr = new FileReader();
        fr.onload = (ev) => {
          state.scanPreview = String(ev.target?.result || "");
        };
        fr.readAsDataURL(state.scanFile);
      }

      syncStartEnabled();
    });

    reportInput.addEventListener("input", syncStartEnabled);

    $("startBtn").addEventListener("click", () => {
      openModal({
        title: "Processing (Demo)",
        bodyHTML: `<p class="small">This is a frontend-only demo. We'll simulate AI inference and show the Analysis Workspace.</p>`,
        footerHTML: `${uiButton({ label: "Cancel", id: "cancelProc" })}${uiButton({
          label: "Continue",
          variant: "primary",
          id: "doProc",
        })}`,
      });

      $("cancelProc").addEventListener("click", closeModal);
      $("doProc").addEventListener("click", () => {
        closeModal();
        mockRunAnalysis();
        setPage("analysis");
      });
    });

    $("goHistory").addEventListener("click", () => setPage("history"));

    state.history.slice(0, 3).forEach((r) => {
      $("act-" + r.id)?.addEventListener("click", () => {
        if (r.status === "processing") {
          openModal({
            title: "Processing",
            bodyHTML: `<p class="small">This case is marked as <b>Processing</b> in the demo table.</p>`,
            footerHTML: uiButton({ label: "Close", variant: "primary", id: "closeWait" }),
          });
          $("closeWait")?.addEventListener("click", closeModal);
          return;
        }

        mockRunAnalysis();
        setPage("analysis");
      });
    });
  }

  function renderAnalysis() {
    if (!state.result) {
      $("view").innerHTML = `<p class="small">No demo result yet. Go to Dashboard and run a demo analysis.</p>`;
      return;
    }

    const r = state.result;

    $("view").innerHTML = `
      <div class="workspace">
        <div class="workspace__bar">
          <div class="workspace__meta">
            <div class="workspace__title">${esc(r.study)}</div>
            <div class="workspace__sub">STUDY ID: ${esc(r.studyId)} · ${esc(r.timestamp)} · <span style="color: rgba(20, 143, 184, 1);">STAT</span></div>
          </div>
          <div style="display:flex; gap: 10px; flex-wrap:wrap;">
            ${uiButton({ label: "Compare Previous", icon: "history", id: "comparePrev" })}
            ${uiButton({ label: "Verify Study", variant: "primary", icon: "check_circle", id: "verifyStudy" })}
          </div>
        </div>

        <div class="workspace__body">
          <div class="viewer">
            <div class="viewer__tools">
              <button class="icon-btn" type="button" aria-label="Zoom">${uiIcon("zoom_in")}</button>
              <button class="icon-btn" type="button" aria-label="Pan">${uiIcon("pan_tool")}</button>
              <button class="icon-btn" type="button" aria-label="Brightness">${uiIcon("brightness_6")}</button>
              <button class="icon-btn" type="button" aria-label="Measure">${uiIcon("straighten")}</button>
              ${uiButton({ label: "AI Overlay", variant: "primary", icon: "visibility", id: "toggleOverlay", extraClass: "" })}
            </div>

            ${state.scanPreview ? `<img class="viewer__img" alt="Uploaded scan preview" src="${esc(state.scanPreview)}" />` : `<img class="viewer__img" alt="Demo diagnostic scan" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD57tZCNaKTyMhcARHi_e-_h-n7kbEwkDiu0bPOhG77MnZk9-Grvq1m0lT1ibcLZrbmk84D_B0As5R3nMwHzzNmBNqB40E0o9u_T49Cjw2KN9nPWd2dBribnY_2lgYQsbde1AKX4Y8NnbtkxyGjc997jLmqBRPTBz7TiVNZIuyjmnY2Le6GUrz5UVhDi_a-pN8lc9vGjkcEsJIONcykPB4qNQF1zdKqQ2UVYPH2WRgXlHtrx0lAe9o0sUJ3AcKDswdk7rd-07p_FxI" />`}

            <div id="overlayBox" class="viewer__overlay" aria-hidden="true">
              <div class="viewer__overlay-label">Cardiomegaly Area</div>
            </div>
            <div id="overlayPulse" class="viewer__pulse" aria-hidden="true"></div>
          </div>

          <div class="findings">
            <div class="findings__header">
              <div class="findings__title">AI Findings</div>
              <div class="findings__ver">v2.4.1</div>
            </div>
            <div class="findings__list">
              ${r.findings
                .map((f, idx) => {
                  const active = idx === 0;
                  const cls = active ? "finding-card finding-card--active" : "finding-card";
                  return `
                    <div class="${cls}">
                      <div class="finding-card__top">
                        <div class="finding-card__name">${esc(f.name)}</div>
                        <div class="finding-card__conf">${Math.round(f.confidence * 100)}% CONF.</div>
                      </div>
                      <div class="finding-card__text">${esc(f.rationale)}</div>
                    </div>
                  `;
                })
                .join("")}
            </div>
          </div>

          <div class="report">
            <div class="report__header">
              <div class="report__title">Human Authored Report</div>
              <div style="display:flex; gap: 6px;">
                <div style="width:10px; height:10px; border-radius:999px; background: var(--discrepancy);"></div>
                <div style="width:10px; height:10px; border-radius:999px; background: var(--omission);"></div>
              </div>
            </div>
            <div class="report__body">
              <div style="text-transform:uppercase; letter-spacing:0.18em; font-size: 12px; font-weight: 900; color: #9ca3af; margin-bottom: 10px;">Narrative Description</div>
              <div style="font-size: 18px; line-height: 1.7; color: #cbd5e1; display:flex; flex-direction:column; gap: 12px;">${r.reportHTML}</div>

              <div class="note">
                <div class="note__title">Discrepancy Detail</div>
                <div class="note__text">${esc(r.discrepancyText)}</div>
                <div class="note__actions">
                  ${uiButton({ label: "Override AI", variant: "danger", id: "overrideAI" })}
                  ${uiButton({ label: "Revise Report", variant: "primary", id: "reviseReport" })}
                </div>
              </div>
            </div>

            <div class="workspace__footer">
              <div class="footer-actions">
                <button class="icon-btn" type="button" aria-label="Chat">${uiIcon("chat_bubble")}</button>
                <button class="icon-btn" type="button" aria-label="Print">${uiIcon("print")}</button>
              </div>
              <div class="footer-actions">
                ${uiButton({ label: "Flag for Review", id: "flag" })}
                ${uiButton({ label: "Sync & Approve", variant: "primary", id: "approve" })}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    const overlayOn = { value: true };
    function setOverlay(v) {
      overlayOn.value = v;
      $("overlayBox").style.display = v ? "block" : "none";
      $("overlayPulse").style.display = v ? "block" : "none";
      $("toggleOverlay").textContent = v ? "AI Overlay" : "Overlay Off";
    }

    setOverlay(true);

    $("toggleOverlay").addEventListener("click", () => setOverlay(!overlayOn.value));

    $("overrideAI").addEventListener("click", () => {
      openModal({
        title: "Override AI (Demo)",
        bodyHTML: `<p class="small">In a real product, this would log an override decision. In this demo, it just updates the status pill.</p>`,
        footerHTML: `${uiButton({ label: "Cancel", id: "ovCancel" })}${uiButton({
          label: "Override",
          variant: "danger",
          id: "ovOk",
        })}`,
      });
      $("ovCancel").addEventListener("click", closeModal);
      $("ovOk").addEventListener("click", () => {
        setStatusPill("warn");
        closeModal();
      });
    });

    $("reviseReport").addEventListener("click", () => {
      openModal({
        title: "Revise Report (Demo)",
        bodyHTML: `<textarea id="reviseText" class="textarea" style="min-height: 220px;" placeholder="Write a revised narrative...">${esc(
          state.reportText ||
            "Lungs are clear bilaterally without focal consolidation. The cardiomediastinal silhouette is within normal limits."
        )}</textarea>`,
        footerHTML: `${uiButton({ label: "Cancel", id: "revCancel" })}${uiButton({
          label: "Save",
          variant: "primary",
          id: "revSave",
        })}`,
      });

      $("revCancel").addEventListener("click", closeModal);
      $("revSave").addEventListener("click", () => {
        state.reportText = $("reviseText").value;
        closeModal();
      });
    });

    $("comparePrev").addEventListener("click", () => {
      openModal({
        title: "Compare Previous",
        bodyHTML: `<p class="small">This is a visual-only placeholder action (no backend integration).</p>`,
        footerHTML: uiButton({ label: "Close", variant: "primary", id: "cmpClose" }),
      });
      $("cmpClose").addEventListener("click", closeModal);
    });

    $("verifyStudy").addEventListener("click", () => setPage("discrepancy"));

    $("flag").addEventListener("click", () => {
      openModal({
        title: "Flag for Review",
        bodyHTML: `<p class="small">Flagging is simulated in demo mode.</p>`,
        footerHTML: uiButton({ label: "OK", variant: "primary", id: "flagOk" }),
      });
      $("flagOk").addEventListener("click", closeModal);
    });

    $("approve").addEventListener("click", () => setPage("export"));
  }

  function renderDiscrepancy() {
    if (!state.result) {
      $("view").innerHTML = `<p class="small">No demo result yet. Go to Dashboard and run a demo analysis.</p>`;
      return;
    }

    const q = state.result.queue;

    $("view").innerHTML = `
      <div style="display:flex; flex-direction:column; gap: 14px;">
        <h1 class="h1" style="font-size: 28px;">Discrepancy Resolution Workspace</h1>
        <div class="small">Resolve each discrepancy before final export.</div>

        ${uiCard({
          bodyHTML: `
            <div class="table-wrap">
              <table class="table" aria-label="Resolution queue">
                <thead>
                  <tr>
                    <th>Finding</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Resolution</th>
                  </tr>
                </thead>
                <tbody>
                  ${q
                    .map((item, idx) => {
                      return `
                        <tr>
                          <td style="font-weight: 900;">${esc(item.key)}</td>
                          <td>${esc(item.category)}</td>
                          <td style="text-transform:uppercase; letter-spacing:0.12em; font-size: 11px; font-weight: 900;">${esc(
                            item.status
                          )}</td>
                          <td>
                            <select class="input" style="padding: 10px;" data-ridx="${idx}">
                              <option value="accept">Accept AI</option>
                              <option value="dismiss">Dismiss</option>
                              <option value="modify">Modify</option>
                            </select>
                          </td>
                        </tr>
                      `;
                    })
                    .join("")}
                </tbody>
              </table>
            </div>
          `,
        })}

        <div style="display:flex; justify-content:flex-end; gap: 10px; flex-wrap:wrap;">
          ${uiButton({ label: "Back", id: "backToAnalysis" })}
          ${uiButton({ label: "Save & Continue Export", variant: "primary", id: "toExport" })}
        </div>
      </div>
    `;

    document.querySelectorAll("select[data-ridx]").forEach((sel) => {
      sel.addEventListener("change", () => {
        state.resolution[sel.getAttribute("data-ridx")] = sel.value;
      });
    });

    $("backToAnalysis").addEventListener("click", () => setPage("analysis"));
    $("toExport").addEventListener("click", () => {
      openExportConfig();
    });
  }

  function openExportConfig() {
    openModal({
      title: "Report Export Configuration",
      bodyHTML: `
        <div class="form-row">
          <label style="display:flex; align-items:center; gap: 10px;"><input id="expHeatmap" type="checkbox" ${state.exportConfig.heatmap ? "checked" : ""} /> Include heatmap overlay</label>
          <label style="display:flex; align-items:center; gap: 10px;"><input id="expSummary" type="checkbox" ${state.exportConfig.summary ? "checked" : ""} /> Include AI summary</label>
          <label style="display:flex; align-items:center; gap: 10px;"><input id="expNarrative" type="checkbox" ${state.exportConfig.narrative ? "checked" : ""} /> Include narrative</label>
          <label style="display:flex; align-items:center; gap: 10px;"><input id="expDiscrepancy" type="checkbox" ${state.exportConfig.discrepancy ? "checked" : ""} /> Include discrepancy log</label>
        </div>
        <div class="small" style="margin-top: 12px;">Demo only: Generates a local JSON file.</div>
      `,
      footerHTML: `${uiButton({ label: "Cancel", id: "expCancel" })}${uiButton({
        label: "Generate Final Export",
        variant: "primary",
        id: "expGo",
      })}`,
    });

    $("expCancel").addEventListener("click", closeModal);
    $("expGo").addEventListener("click", () => {
      state.exportConfig = {
        heatmap: $("expHeatmap").checked,
        summary: $("expSummary").checked,
        narrative: $("expNarrative").checked,
        discrepancy: $("expDiscrepancy").checked,
      };

      closeModal();
      setPage("export");
    });
  }

  function renderExport() {
    if (!state.result) {
      $("view").innerHTML = `<p class="small">No demo result yet. Go to Dashboard and run a demo analysis.</p>`;
      return;
    }

    $("view").innerHTML = `
      <div style="max-width: 920px; margin: 0 auto;">
        ${uiCard({
          bodyHTML: `
            <div style="display:flex; align-items:flex-start; justify-content:space-between; gap: 12px; flex-wrap:wrap;">
              <div>
                <h1 class="h1" style="font-size: 26px; margin: 0;">Final Exported PDF Layout</h1>
                <div class="small" style="margin-top: 6px;">Generated document preview for archive and compliance (static demo).</div>
              </div>
              ${uiButton({ label: "Download JSON Bundle", variant: "primary", id: "download" })}
            </div>

            <div style="margin-top: 18px; display:grid; grid-template-columns: 1fr; gap: 10px;">
              <div><b>Study:</b> ${esc(state.result.study)}</div>
              <div><b>Generated at:</b> ${esc(new Date().toLocaleString())}</div>
              <div><b>Export options:</b> <span style="font-family: var(--mono); font-size: 12px;">${esc(
                JSON.stringify(state.exportConfig)
              )}</span></div>
              <div><b>Resolution:</b> <span style="font-family: var(--mono); font-size: 12px;">${esc(
                JSON.stringify(state.resolution)
              )}</span></div>
              <div><b>Comparison summary:</b> ${esc(state.result.discrepancyText)}</div>
            </div>
          `,
        })}
      </div>
    `;

    $("download").addEventListener("click", () => {
      const payload = {
        exportConfig: state.exportConfig,
        resolution: state.resolution,
        result: state.result,
      };

      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
      a.download = `stitch_demo_export_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();

      state.history.unshift({
        id: "EXPORT-" + String(Date.now()).slice(-5),
        type: "Export Bundle",
        patient: "EXPORT",
        timestamp: new Date().toLocaleString(),
        status: "verified",
      });
    });
  }

  function renderHistory() {
    $("view").innerHTML = `
      <div style="margin-bottom: 18px;">
        <h1 class="h1" style="font-size: 30px;">History & Archive</h1>
        <div class="small" style="margin-top: 6px;">Comprehensive audit log of all demo verifications.</div>
      </div>

      ${uiCard({
        bodyHTML: `
          <div class="table-wrap">
            <table class="table" aria-label="History">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Patient</th>
                  <th>Timestamp</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${state.history
                  .map((r) => {
                    return `
                      <tr>
                        <td style="font-family: var(--mono); font-weight: 800;">${esc(r.id)}</td>
                        <td>${esc(r.patient)}</td>
                        <td style="color: var(--muted);">${esc(r.timestamp)}</td>
                        <td>${uiBadge(r.status)}</td>
                        <td>${uiButton({ label: "Open", variant: "ghost", id: `h-${esc(r.id)}` })}</td>
                      </tr>
                    `;
                  })
                  .join("")}
              </tbody>
            </table>
          </div>
        `,
      })}
    `;

    state.history.forEach((r) => {
      $("h-" + r.id)?.addEventListener("click", () => {
        mockRunAnalysis();
        setPage("analysis");
      });
    });
  }

  function renderHelp() {
    $("view").innerHTML = `
      <div style="text-align:center; padding: 26px; border-radius: 18px; background: linear-gradient(135deg, ${
        "rgba(31,102,173,1)"
      }, rgba(26,67,110,1)); color: white; box-shadow: var(--shadow);">
        <h1 class="h1" style="font-size: 30px;">How can we help you today?</h1>
        <div class="small" style="color: rgba(255,255,255,0.85); margin-top: 10px;">This is a frontend-only recreation of the Stitch demo (no backend integration).</div>
        <div style="max-width: 720px; margin: 18px auto 0 auto;">
          <input class="input" placeholder="Search docs..." />
        </div>
      </div>

      <div class="grid" style="grid-template-columns: 1fr; margin-top: 18px;">
        ${uiCard({
          bodyHTML: `
            <div style="display:flex; flex-direction:column; gap: 10px;">
              <div style="font-weight: 1000;">Quick Start</div>
              <div class="small">1) Open <b>Dashboard</b> and upload any image + paste any text.</div>
              <div class="small">2) Click <b>Start Demo Analysis</b> to see the Analysis Workspace.</div>
              <div class="small">3) Navigate to <b>Discrepancy Resolution</b> and then <b>Final Export</b>.</div>
            </div>
          `,
        })}
      </div>
    `;
  }

  function bindGlobal() {
    $("modalClose").addEventListener("click", closeModal);
    $("backdrop").addEventListener("click", closeModal);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });

    // Sidebar (mobile)
    $("sidebarToggle")?.addEventListener("click", () => {
      const sb = getSidebar();
      const open = sb?.getAttribute("data-open") === "true";
      showSidebar(!open);
    });

    ensureSidebarBackdrop().addEventListener("click", () => showSidebar(false));
    window.addEventListener("resize", () => {
      if (!isMobile()) showSidebar(false);
    });

    $("newAnalysisBtn").addEventListener("click", () => {
      state.scanFile = null;
      state.scanPreview = "";
      state.reportText = "";
      state.result = null;
      state.resolution = {};
      setStatusPill(null);
      setPage("upload");
    });

    $("openSignIn").addEventListener("click", () => {
      openModal({
        title: "Sign In (Demo)",
        bodyHTML: `
          <div class="form-row">
            <div>
              <div class="small" style="margin-bottom: 6px; font-weight: 900;">Institutional Email</div>
              <input id="loginEmail" class="input" placeholder="physician@hospital.org" />
            </div>
            <div>
              <div class="small" style="margin-bottom: 6px; font-weight: 900;">Role</div>
              <select id="loginRole" class="input">
                <option>Radiologist</option>
                <option>Resident</option>
                <option>Admin</option>
              </select>
            </div>
          </div>
          <div class="small" style="margin-top: 10px;">No authentication is performed. This only updates the demo header.</div>
        `,
        footerHTML: `${uiButton({ label: "Cancel", id: "loginCancel" })}${uiButton({
          label: "Continue",
          variant: "primary",
          id: "loginOk",
        })}`,
      });

      $("loginCancel").addEventListener("click", closeModal);
      $("loginOk").addEventListener("click", () => {
        const email = $("loginEmail").value.trim();
        const role = $("loginRole").value;
        state.role = role;
        state.user = {
          name: email ? email.split("@")[0] : "RAVEN Operator",
          title: role,
        };
        $("userName").textContent = state.user.name;
        $("userRole").textContent = state.user.title;
        closeModal();
      });
    });
  }

  function init() {
    bindGlobal();
    renderNav();
    setStatusPill(null);
    setPage("upload");
  }

  init();
})();
