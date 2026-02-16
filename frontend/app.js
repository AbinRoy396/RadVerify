(() => {
  const API_BASE = "http://localhost:8000";
  const API_KEY = "radverify_secret_key";

  const state = {
    authenticated: false,
    role: "Radiologist",
    email: "",
    page: "upload",
    file: null,
    reportText: "",
    imagePreview: "",
    result: null,
    history: [],
    localArchive: [],
    exportConfig: { heatmap: true, summary: true, narrative: true, discrepancy: true },
    resolution: {},
  };

  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const escapeRegex = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const BASE_NAV = [
    ["upload", "Dashboard", "dashboard"],
    ["analysis", "Analysis Workspace", "biotech"],
    ["discrepancy-resolution", "Discrepancy Resolution", "rule_settings"],
    ["export-final", "Final Export", "picture_as_pdf"],
    ["history", "History & Archive", "history"],
    ["help", "Help Center", "help_center"],
  ];
  const RESIDENT_NAV = [
    ["peer-review", "Peer Review Queue", "fact_check"],
    ["student-performance", "Performance Report", "insights"],
    ["badges", "Achievements", "workspace_premium"],
    ["leaderboard", "Leaderboard", "emoji_events"],
  ];
  const ADMIN_NAV = [
    ["analytics", "Comparative Analytics", "analytics"],
    ["model-performance", "Model Dashboard", "monitoring"],
    ["ai-sensitivity", "AI Sensitivity", "tune"],
    ["protocol-testing", "Protocol Testing", "science"],
    ["audit-logs", "System Audit Logs", "receipt_long"],
    ["settings", "Settings", "settings"],
  ];

  const ALL_SECTIONS = [
    "upload", "analysis", "history", "analytics", "settings", "help",
    "discrepancy-resolution", "export-final", "peer-review", "student-performance", "badges", "leaderboard",
    "model-performance", "ai-sensitivity", "protocol-testing", "audit-logs"
  ];

  function navForRole() {
    if (state.role === "Resident") return [...BASE_NAV, ...RESIDENT_NAV];
    if (state.role === "Admin") return [...BASE_NAV, ...ADMIN_NAV];
    return [...BASE_NAV, ["analytics", "Comparative Analytics", "analytics"], ["settings", "Settings", "settings"]];
  }

  function canAccess(page) { return navForRole().some((n) => n[0] === page); }

  function show(el, v) {
    if (!el) return;
    el.classList.toggle("hidden", !v);
    if (["processingOverlay", "onboardingModal", "exportModal"].includes(el.id)) {
      el.classList.toggle("flex", v);
    }
  }

  async function apiGet(path) {
    const r = await fetch(API_BASE + path, { headers: { "X-API-Key": API_KEY } });
    if (!r.ok) {
      let msg = "Request failed";
      try { msg = (await r.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return r.json();
  }

  async function apiVerify() {
    const fd = new FormData();
    fd.append("scan", state.file);
    fd.append("report", state.reportText);
    fd.append("enhance", "true");
    const r = await fetch(API_BASE + "/verify", { method: "POST", headers: { "X-API-Key": API_KEY }, body: fd });
    if (!r.ok) {
      let msg = "Verification failed";
      try { msg = (await r.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return r.json();
  }

  function setPage(page) {
    if (!canAccess(page)) return;
    state.page = page;

    ALL_SECTIONS.forEach((k) => {
      const sec = $("page-" + k);
      if (sec) sec.classList.toggle("hidden", k !== page);
    });

    navForRole().forEach(([key]) => {
      const n = $("nav-" + key);
      if (!n) return;
      n.className = key === page
        ? "flex items-center gap-3 px-3 py-2.5 rounded-lg bg-primary/10 text-primary group"
        : "flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#657586] hover:bg-[#f0f2f4] transition-colors";
    });

    const title = {
      upload: ["Upload Portal", "Clinical input and processing"],
      analysis: ["Analysis Workspace", "AI findings and report comparison"],
      "discrepancy-resolution": ["Discrepancy Resolution Workspace", "Accept, dismiss, or modify AI findings"],
      "export-final": ["Final Exported PDF Layout", "Finalize and archive verified report"],
      history: ["History & Archive", "Compliance-grade audit retrieval"],
      "peer-review": ["Peer Review Oversight Queue", "Senior review for resident submissions"],
      "student-performance": ["Individual Student Performance", "Accuracy and learning trajectory"],
      badges: ["Achievements & Badges Gallery", "Milestones and recognition"],
      leaderboard: ["Resident Leaderboard", "Ranking by accuracy and volume"],
      analytics: ["Comparative Analytics Dashboard", "Cross-modality discrepancy trends"],
      "model-performance": ["AI Model Performance Dashboard", "Monitor drift and performance"],
      "ai-sensitivity": ["AI Sensitivity Settings", "Adjust detection thresholds"],
      "protocol-testing": ["Protocol Simulation & Testing", "Validate protocol changes"],
      "audit-logs": ["System Audit Logs", "Traceability and accountability"],
      settings: ["Individual Settings", "Profile and preferences"],
      help: ["Help & Documentation Center", "Tutorials and support channels"],
    };

    $("pageTitle").textContent = title[page]?.[0] || "RAVEN";
    $("pageSub").textContent = title[page]?.[1] || "";
  }

  function setStatusPill() {
    const pill = $("statusPill");
    if (!state.result) {
      pill.classList.add("hidden");
      return;
    }

    const counts = state.result?.verification_results?.discrepancy_counts || {};
    const bad = Number(counts.mismatches || 0);
    const warn = Number(counts.omissions || 0) + Number(counts.overstatements || 0);

    pill.className = "px-3 py-1 rounded-full text-xs font-bold uppercase";
    if (bad > 0) {
      pill.classList.add("bg-red-100", "text-red-700");
      pill.textContent = "Discrepancy";
    } else if (warn > 0) {
      pill.classList.add("bg-amber-100", "text-amber-700");
      pill.textContent = "Review Needed";
    } else {
      pill.classList.add("bg-green-100", "text-green-700");
      pill.textContent = "Match";
    }
  }

  function renderNav() {
    $("navMenu").innerHTML = navForRole().map(([key, label, icon], idx) => `
      <button id="nav-${key}" class="flex items-center gap-3 px-3 py-2.5 rounded-lg ${idx === 0 ? "bg-primary/10 text-primary" : "text-[#657586] hover:bg-[#f0f2f4]"} transition-colors">
        <span class="material-symbols-outlined text-[22px]">${icon}</span>
        <span class="text-sm font-${idx === 0 ? "semibold" : "medium"}">${label}</span>
      </button>`).join("");

    navForRole().forEach(([key]) => {
      const node = $("nav-" + key);
      if (!node) return;
      node.addEventListener("click", async () => {
        if (["analysis", "discrepancy-resolution", "export-final"].includes(key) && !state.result) {
          alert("Run analysis first from Upload Portal.");
          return;
        }
        setPage(key);
        if (key === "history") await loadHistory();
      });
    });
  }

  function flattenFindings() {
    const structures = state.result?.ai_findings?.structures_detected || {};
    const cmp = state.result?.verification_results?.structure_comparisons || {};
    const list = [];
    Object.entries(structures).forEach(([cat, map]) => {
      Object.entries(map || {}).forEach(([name, val]) => {
        list.push({ category: cat, name, confidence: Number(val?.confidence || 0), present: Boolean(val?.present), status: cmp?.[cat]?.[name]?.status || "not_assessed" });
      });
    });
    return list.sort((a, b) => b.confidence - a.confidence);
  }

  function unresolvedDiscrepancies() {
    return flattenFindings().filter((f) => ["mismatch", "omission", "overstatement"].includes(f.status));
  }

  function highlightReport() {
    let html = esc(state.reportText).replaceAll("\n", "<br>");
    const cmp = state.result?.verification_results?.structure_comparisons || {};
    const mismatch = [];
    const omission = [];

    Object.values(cmp).forEach((cat) => {
      Object.entries(cat || {}).forEach(([k, v]) => {
        const term = k.replaceAll("_", " ");
        if (v?.status === "mismatch") mismatch.push(term);
        if (v?.status === "omission") omission.push(term);
      });
    });

    mismatch.sort((a, b) => b.length - a.length).forEach((term) => {
      const re = new RegExp("\\b" + escapeRegex(term) + "\\b", "ig");
      html = html.replace(re, (m) => `<span class="hl-bad">${m}</span>`);
    });

    if (omission.length) {
      html += '<div class="mt-4">' + [...new Set(omission)].slice(0, 8).map((t) => `<span class="hl-warn mr-2">Potential omission: ${esc(t)}</span>`).join("") + "</div>";
    }

    return html;
  }
  function renderUpload() {
    $("page-upload").innerHTML = `
      <div class="max-w-2xl"><h3 class="text-3xl font-black tracking-tight text-[#121417] font-display">Verify New Medical Scans</h3><p class="text-[#657586] mt-2 text-base">Pair medical imagery with human-written reports for high-precision cross-validation.</p></div>
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="flex flex-col gap-3"><p class="text-sm font-bold text-[#121417] flex items-center gap-2"><span class="material-symbols-outlined text-primary text-lg">image</span>1. Upload Medical Scans</p>
          <label for="scanInput" class="dashed-border bg-white min-h-[300px] flex flex-col items-center justify-center p-8 text-center cursor-pointer"><div class="size-16 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4"><span class="material-symbols-outlined text-3xl">upload_file</span></div><h4 class="text-base font-bold text-[#121417]">Drag & drop files here</h4><p class="text-sm text-[#657586] mt-1 mb-4">Support for DICOM, JPEG, PNG</p><p id="scanName" class="text-xs font-bold text-primary"></p><input id="scanInput" type="file" accept="image/*,.dcm" class="hidden" /></label>
        </div>
        <div class="flex flex-col gap-3"><p class="text-sm font-bold text-[#121417] flex items-center gap-2"><span class="material-symbols-outlined text-primary text-lg">subject</span>2. Human-Written Radiology Report</p><textarea id="reportInput" class="w-full min-h-[300px] rounded-xl border border-[#dce0e5] bg-white p-5 text-sm" placeholder="Paste the official radiology report text here..."></textarea></div>
      </div>
      <div class="flex items-center justify-between p-4 bg-primary/5 rounded-xl border border-primary/20"><p class="text-sm font-medium text-[#1f66ad]">Ensure all patient identifiers are redacted if required by local policy.</p><button id="startBtn" class="bg-primary text-white px-8 py-3 rounded-lg text-base font-extrabold disabled:opacity-50" disabled>Start AI Analysis</button></div>
      <p id="uploadMsg" class="text-sm"></p>
      <div class="space-y-4"><div class="flex items-center justify-between"><h4 class="text-lg font-bold">Recent Activity</h4><button id="openHistoryBtn" class="text-primary text-sm font-bold hover:underline">View Full History</button></div><div class="bg-white rounded-xl border border-[#dce0e5] overflow-hidden"><table class="w-full text-left border-collapse"><thead><tr class="bg-[#fcfcfd] border-b border-[#dce0e5]"><th class="px-6 py-4 text-xs font-bold uppercase text-[#657586]">Case ID</th><th class="px-6 py-4 text-xs font-bold uppercase text-[#657586]">Patient Ref</th><th class="px-6 py-4 text-xs font-bold uppercase text-[#657586]">Risk</th><th class="px-6 py-4 text-xs font-bold uppercase text-[#657586]">Action</th></tr></thead><tbody id="recentRows" class="divide-y divide-[#dce0e5]"></tbody></table></div></div>`;

    const scanInput = $("scanInput");
    const reportInput = $("reportInput");
    const startBtn = $("startBtn");
    const syncEnable = () => (startBtn.disabled = !(state.file && reportInput.value.trim()));

    scanInput.addEventListener("change", (e) => {
      state.file = e.target.files?.[0] || null;
      $("scanName").textContent = state.file ? `Selected: ${state.file.name}` : "";
      if (state.file) {
        const fr = new FileReader();
        fr.onload = (ev) => (state.imagePreview = ev.target?.result || "");
        fr.readAsDataURL(state.file);
      }
      syncEnable();
    });
    reportInput.addEventListener("input", syncEnable);

    $("openHistoryBtn").addEventListener("click", async () => {
      setPage("history");
      await loadHistory();
    });

    startBtn.addEventListener("click", async () => {
      state.reportText = reportInput.value.trim();
      $("uploadMsg").className = "text-sm text-[#657586]";
      $("uploadMsg").textContent = "Initializing processing...";
      show($("processingOverlay"), true);
      try {
        await sleep(600);
        startBtn.disabled = true;
        state.result = await apiVerify();
        setStatusPill();
        renderAnalysis();
        renderDiscrepancyResolution();
        renderExportFinal();
        $("uploadMsg").className = "text-sm text-green-600";
        $("uploadMsg").textContent = "Analysis completed. Opening workspace...";
        setPage("analysis");
      } catch (err) {
        $("uploadMsg").className = "text-sm text-red-600";
        $("uploadMsg").textContent = err.message;
      } finally {
        show($("processingOverlay"), false);
        startBtn.disabled = false;
      }
    });
    renderRecent();
  }

  function renderAnalysis() {
    const vr = state.result?.verification_results || {};
    const counts = vr?.discrepancy_counts || {};
    const findings = flattenFindings().filter((f) => f.present || f.confidence >= 0.5).slice(0, 15);

    $("page-analysis").innerHTML = `
      <div class="h-[calc(100vh-7rem)] flex flex-col bg-[#17191c] text-slate-100 rounded-xl overflow-hidden">
        <div class="flex items-center justify-between px-6 py-3 bg-[#1e2124] border-b border-slate-800"><div><h1 class="font-bold text-lg">${esc(state.file?.name || "Current Study")}</h1><p class="text-xs text-slate-400">Agreement ${vr.agreement_rate != null ? Math.round(vr.agreement_rate * 100) : "-"}% · Risk ${esc(vr.risk_level || "-")}</p></div><div class="flex gap-2 text-xs"><span class="px-2 py-1 rounded bg-red-500/20 text-red-300">Mismatch ${Number(counts.mismatches || 0)}</span><span class="px-2 py-1 rounded bg-amber-500/20 text-amber-300">Omission ${Number(counts.omissions || 0)}</span></div></div>
        <div class="flex flex-1 overflow-hidden">
          <div class="flex-[1.45] diagnostic-viewer p-6 border-r border-slate-800 flex items-center justify-center">${state.imagePreview ? `<img src="${state.imagePreview}" class="max-w-full max-h-full rounded shadow-2xl opacity-80 mix-blend-screen" />` : '<p class="text-slate-400">No preview</p>'}</div>
          <div class="w-80 bg-[#1a1c1e] border-r border-slate-800 p-4 overflow-auto scrollbar-thin"><h3 class="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3">AI Findings</h3>${findings.map((f) => `<div class="mb-3 p-3 rounded-lg border-l-4 ${["mismatch", "omission", "overstatement"].includes(f.status) ? "border-red-400 bg-red-500/5" : "border-cyan-400 bg-slate-800/40"}"><div class="flex justify-between"><b class="text-sm">${esc(f.name.replaceAll("_", " "))}</b><span class="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-bold">${Math.round(f.confidence * 100)}%</span></div><p class="text-xs text-slate-400 mt-1">${esc(f.category)}</p><p class="text-xs uppercase">${esc(f.status)}</p></div>`).join("")}</div>
          <div class="flex-1 bg-[#1e2124] p-6 overflow-auto scrollbar-thin"><h3 class="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Human Authored Report</h3><div class="text-base leading-relaxed">${highlightReport()}</div><div class="mt-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl"><h4 class="text-red-300 text-xs font-bold uppercase mb-2">Discrepancy Detail</h4><p class="text-sm text-slate-300">${esc(state.result?.comparison_report_text || "")}</p><div class="flex gap-2 mt-3"><button id="openResolutionBtn" class="bg-red-500 text-white text-xs font-bold px-3 py-1 rounded">Open Resolution Workspace</button><button id="openExportFlowBtn" class="bg-cyan-600 text-white text-xs font-bold px-3 py-1 rounded">Proceed to Export</button></div></div></div>
        </div>
      </div>`;

    $("openResolutionBtn")?.addEventListener("click", () => {
      renderDiscrepancyResolution();
      setPage("discrepancy-resolution");
    });
    $("openExportFlowBtn")?.addEventListener("click", () => show($("exportModal"), true));
  }

  function renderDiscrepancyResolution() {
    const list = unresolvedDiscrepancies();
    $("page-discrepancy-resolution").innerHTML = `
      <div class="space-y-4"><h3 class="text-2xl font-display font-bold">Discrepancy Resolution Workspace</h3><p class="text-[#657586]">Resolve each discrepancy before final export.</p>
      <div class="bg-white rounded-xl border border-[#dce0e5] overflow-hidden"><table class="w-full text-sm"><thead class="bg-[#fcfcfd]"><tr><th class="px-4 py-3 text-left">Finding</th><th class="px-4 py-3 text-left">Category</th><th class="px-4 py-3 text-left">Status</th><th class="px-4 py-3 text-left">Resolution</th></tr></thead><tbody>${list.map((item, idx) => `<tr class="border-t border-[#e6eaf0]"><td class="px-4 py-3 font-semibold">${esc(item.name.replaceAll("_", " "))}</td><td class="px-4 py-3">${esc(item.category)}</td><td class="px-4 py-3 uppercase text-xs">${esc(item.status)}</td><td class="px-4 py-3"><select data-ridx="${idx}" class="resolution-select rounded-lg border border-[#dce0e5] px-2 py-1 text-xs"><option value="accept">Accept AI</option><option value="dismiss">Dismiss</option><option value="modify">Modify</option></select></td></tr>`).join("") || '<tr><td class="px-4 py-4" colspan="4">No active discrepancies.</td></tr>'}</tbody></table></div><div class="flex justify-end gap-2"><button id="backToAnalysisBtn" class="px-4 py-2 border border-[#dce0e5] rounded-lg font-semibold">Back</button><button id="saveResolutionBtn" class="px-4 py-2 bg-primary text-white rounded-lg font-bold">Save & Continue Export</button></div></div>`;

    document.querySelectorAll(".resolution-select").forEach((sel) => {
      sel.addEventListener("change", () => {
        state.resolution[sel.getAttribute("data-ridx")] = sel.value;
      });
    });

    $("backToAnalysisBtn")?.addEventListener("click", () => setPage("analysis"));
    $("saveResolutionBtn")?.addEventListener("click", () => show($("exportModal"), true));
  }

  function renderExportFinal() {
    $("page-export-final").innerHTML = `
      <div class="max-w-4xl mx-auto bg-white border border-[#dce0e5] rounded-xl shadow-sm p-8"><div class="flex items-center justify-between border-b border-[#e8edf2] pb-4 mb-6"><div><h2 class="text-2xl font-display font-bold">Final Exported PDF Layout</h2><p class="text-[#657586] text-sm">Generated document preview for archive and compliance.</p></div><button id="downloadFinalBtn" class="px-4 py-2 bg-primary text-white rounded-lg font-bold">Download JSON Bundle</button></div><div class="space-y-4 text-sm"><p><b>Study:</b> ${esc(state.file?.name || "-")}</p><p><b>Generated At:</b> ${new Date().toLocaleString()}</p><p><b>Comparison Summary:</b> ${esc(state.result?.comparison_report_text || "-")}</p></div></div>`;

    $("downloadFinalBtn")?.addEventListener("click", () => {
      const payload = { export_config: state.exportConfig, resolution: state.resolution, result: state.result };
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
      a.download = `raven_export_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
  }
  async function loadHistory() {
    try { state.history = await apiGet("/history?limit=100"); } catch {}
    renderHistory();
  }

  function mergedArchive() {
    const remote = state.history.map((h) => ({
      id: h.id || h.case_id,
      patient_id: h.patient_id,
      created_at: h.created_at,
      risk: String(h?.verification_results?.risk_level || "-").toUpperCase(),
      source: "API",
    }));
    const local = state.localArchive.map((h, idx) => ({ id: `LOCAL-${idx + 1}`, ...h, source: "Local Export" }));
    return [...local, ...remote];
  }

  function renderHistory() {
    const rows = mergedArchive();
    $("page-history").innerHTML = `
      <div class="mb-8"><h2 class="text-3xl font-black tracking-tight text-[#121516]">History & Archive</h2><p class="text-[#6a7b81] mt-1">Comprehensive audit log of all AI-assisted radiology verifications.</p></div>
      <div class="bg-white border border-gray-200 rounded-xl overflow-hidden"><div class="overflow-x-auto"><table class="w-full text-left border-collapse"><thead><tr class="bg-gray-50 text-[11px] uppercase font-bold tracking-wider text-[#657586]"><th class="px-6 py-4 border-b">Case ID</th><th class="px-6 py-4 border-b">Patient</th><th class="px-6 py-4 border-b">Risk</th><th class="px-6 py-4 border-b">Created</th><th class="px-6 py-4 border-b">Source</th></tr></thead><tbody>${rows.map((h) => {
      const risk = String(h.risk || "-").toUpperCase();
      const rc = risk === "HIGH" ? "bg-red-50 text-red-700" : risk === "MEDIUM" ? "bg-orange-50 text-orange-700" : risk === "LOW" ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-600";
      return `<tr class="hover:bg-gray-50 transition-colors border-t border-gray-100"><td class="px-6 py-4 text-sm font-mono">${esc(h.id || "-")}</td><td class="px-6 py-4 text-sm">${esc(h.patient_id || "-")}</td><td class="px-6 py-4"><span class="inline-flex px-2.5 py-1 rounded-full text-[10px] font-black ${rc}">${esc(risk)}</span></td><td class="px-6 py-4 text-sm text-[#657586]">${esc(h.created_at || "-")}</td><td class="px-6 py-4 text-sm">${esc(h.source || "-")}</td></tr>`;
    }).join("") || '<tr><td colspan="5" class="px-6 py-6 text-center text-[#657586]">No records found.</td></tr>'}</tbody></table></div></div>`;
  }

  function renderAnalytics() {
    const rows = mergedArchive();
    const risks = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    rows.forEach((h) => { if (risks[h.risk] !== undefined) risks[h.risk] += 1; });
    const total = rows.length || 1;
    const pct = (v) => Math.round((v / total) * 100);

    $("page-analytics").innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"><div class="bg-white p-6 rounded-xl border"><p class="text-sm font-bold text-[#658686]">Total Scans</p><h3 class="text-3xl font-extrabold mt-2">${rows.length}</h3></div><div class="bg-white p-6 rounded-xl border"><p class="text-sm font-bold text-[#658686]">High Risk</p><h3 class="text-3xl font-extrabold mt-2 text-[#e73108]">${risks.HIGH}</h3></div><div class="bg-white p-6 rounded-xl border"><p class="text-sm font-bold text-[#658686]">Low Risk</p><h3 class="text-3xl font-extrabold mt-2 text-[#078832]">${risks.LOW}</h3></div></div>
      <div class="bg-white p-8 rounded-xl border max-w-4xl space-y-4"><h4 class="text-lg font-bold">Discrepancy Distribution</h4><div><div class="flex justify-between text-xs font-bold mb-1"><span>High</span><span>${pct(risks.HIGH)}%</span></div><div class="h-3 bg-[#f0f4f4] rounded-full overflow-hidden"><div class="h-full bg-[#e73108]" style="width:${pct(risks.HIGH)}%"></div></div></div><div><div class="flex justify-between text-xs font-bold mb-1"><span>Medium</span><span>${pct(risks.MEDIUM)}%</span></div><div class="h-3 bg-[#f0f4f4] rounded-full overflow-hidden"><div class="h-full bg-[#e68a00]" style="width:${pct(risks.MEDIUM)}%"></div></div></div><div><div class="flex justify-between text-xs font-bold mb-1"><span>Low</span><span>${pct(risks.LOW)}%</span></div><div class="h-3 bg-[#f0f4f4] rounded-full overflow-hidden"><div class="h-full bg-[#178282]" style="width:${pct(risks.LOW)}%"></div></div></div></div>`;
  }

  function renderSimplePage(id, title, content) {
    $(id).innerHTML = `<h3 class="text-2xl font-display font-bold mb-4">${title}</h3><div class="bg-white rounded-xl border p-6">${content}</div>`;
  }

  function renderRolePages() {
    renderSimplePage("page-peer-review", "Peer Review Oversight Queue", "<p class='text-sm text-[#657586]'>Resident verified reports queue for senior review.</p>");
    renderSimplePage("page-student-performance", "Individual Student Performance Report", "<p class='text-sm text-[#657586]'>Track resident accuracy and throughput over time.</p>");
    renderSimplePage("page-badges", "Achievements & Badges Gallery", "<p class='text-sm text-[#657586]'>Milestones, streaks, and quality badges.</p>");
    renderSimplePage("page-leaderboard", "Resident Leaderboard", "<p class='text-sm text-[#657586]'>Department ranking by accuracy and volume.</p>");
    renderSimplePage("page-model-performance", "AI Model Performance Dashboard", "<p class='text-sm text-[#657586]'>Monitor drift, precision, recall, and model versions.</p>");
    renderSimplePage("page-ai-sensitivity", "AI Sensitivity Settings", "<p class='text-sm text-[#657586]'>Tune thresholds to balance false positives and misses.</p>");
    renderSimplePage("page-protocol-testing", "Protocol Simulation & Testing View", "<p class='text-sm text-[#657586]'>Evaluate protocol changes before deployment.</p>");
    renderSimplePage("page-audit-logs", "System Audit Logs", "<p class='text-sm text-[#657586]'>Immutable action logs for compliance and accountability.</p>");
  }

  function renderSettings() {
    renderSimplePage("page-settings", "Individual Settings", `<p class='text-sm text-[#657586]'>User: ${esc(state.email || "-")} · Role: ${esc(state.role)}</p>`);
  }

  function renderHelp() {
    $("page-help").innerHTML = `<div class="max-w-[1280px] mx-auto w-full"><div class="text-center mb-10 py-10 rounded-2xl bg-gradient-to-br from-primary to-[#1a436e] text-white shadow-xl"><h1 class="tracking-tight text-3xl font-bold mb-4">How can we help you today?</h1><div class="max-w-2xl mx-auto px-6"><input class="w-full px-4 py-3 bg-white border-none rounded-xl text-slate-900 text-lg" placeholder="Search docs..." type="text"></div></div></div>`;
  }

  async function renderRecent() {
    const tbody = $("recentRows");
    if (!tbody) return;
    try {
      const items = await apiGet("/history?limit=5");
      state.history = items;
      tbody.innerHTML = items.map((h) => {
        const id = h.id || h.case_id || "-";
        const risk = String(h?.verification_results?.risk_level || "-").toUpperCase();
        const cls = risk === "HIGH" ? "bg-red-100 text-red-700" : risk === "MEDIUM" ? "bg-orange-100 text-orange-700" : risk === "LOW" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600";
        return `<tr class="hover:bg-primary/[0.01] transition-colors"><td class="px-6 py-4 text-sm font-bold">#${esc(id)}</td><td class="px-6 py-4 text-sm">${esc(h.patient_id || "-")}</td><td class="px-6 py-4"><span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${cls} text-xs font-bold">${esc(risk)}</span></td><td class="px-6 py-4"><button class="text-primary hover:text-primary/70 font-bold text-sm recent-open">Open</button></td></tr>`;
      }).join("") || '<tr><td colspan="4" class="px-6 py-4 text-sm text-[#657586]">No activity yet.</td></tr>';

      document.querySelectorAll(".recent-open").forEach((b) => b.addEventListener("click", async () => {
        setPage("history");
        await loadHistory();
      }));
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="4" class="px-6 py-4 text-sm text-red-600">${esc(err.message)}</td></tr>`;
    }
  }
  async function healthCheck() {
    try {
      const r = await fetch(API_BASE + "/health");
      $("apiStatus").textContent = r.ok ? "Online (FastAPI connected)" : "Unavailable";
      $("apiStatus").className = r.ok ? "text-[11px] text-green-600 leading-relaxed" : "text-[11px] text-red-600 leading-relaxed";
    } catch {
      $("apiStatus").textContent = "Unavailable";
      $("apiStatus").className = "text-[11px] text-red-600 leading-relaxed";
    }
  }

  function bindGlobal() {
    $("newAnalysisBtn").addEventListener("click", () => {
      state.file = null;
      state.reportText = "";
      state.imagePreview = "";
      state.result = null;
      state.resolution = {};
      setStatusPill();
      renderUpload();
      setPage("upload");
    });

    $("cancelExportBtn").addEventListener("click", () => show($("exportModal"), false));
    $("confirmExportBtn").addEventListener("click", () => {
      state.exportConfig = {
        heatmap: $("expHeatmap").checked,
        summary: $("expSummary").checked,
        narrative: $("expNarrative").checked,
        discrepancy: $("expDiscrepancy").checked,
      };

      state.localArchive.unshift({
        patient_id: `EXPORT_${Date.now()}`,
        created_at: new Date().toLocaleString(),
        risk: String(state.result?.verification_results?.risk_level || "-").toUpperCase(),
      });

      show($("exportModal"), false);
      renderExportFinal();
      setPage("export-final");
    });
  }

  function bindAuth() {
    show($("signInScreen"), true);
    $("mainSidebar").classList.add("hidden");
    $("mainApp").classList.add("hidden");

    $("loginBtn").addEventListener("click", () => {
      const email = $("loginEmail").value.trim();
      const pass = $("loginPassword").value;
      const role = $("loginRole").value;
      if (!email || !pass) {
        $("loginError").textContent = "Enter email and password.";
        return;
      }

      state.authenticated = true;
      state.email = email;
      state.role = role;

      renderNav();
      renderSettings();
      renderRolePages();
      setPage("upload");

      show($("signInScreen"), false);
      $("mainSidebar").classList.remove("hidden");
      $("mainApp").classList.remove("hidden");
      show($("onboardingModal"), true);
    });

    $("onboardingCloseBtn").addEventListener("click", () => show($("onboardingModal"), false));
  }

  async function init() {
    bindGlobal();
    renderUpload();
    renderAnalysis();
    renderDiscrepancyResolution();
    renderExportFinal();
    renderHistory();
    renderAnalytics();
    renderSettings();
    renderHelp();
    renderRolePages();
    setStatusPill();
    await healthCheck();
    try { state.history = await apiGet("/history?limit=100"); } catch {}
    bindAuth();
  }

  init();
})();
