(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { file: null, health: null, result: null, maxBytes: 10 * 1024 * 1024 };
  const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

  const fileInput = $("fileInput");
  const dropzone = $("dropzone");
  const processBtn = $("processBtn");
  const statusEl = $("status");

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.classList.toggle("error", isError);
  }

  function formatBytes(n) {
    if (n == null) return "n/a";
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / 1024 / 1024).toFixed(2)} MB`;
  }

  async function loadHealth() {
    try {
      const res = await fetch("/api/health");
      const h = await res.json();
      state.health = h;
      state.maxBytes = h.max_upload_mb * 1024 * 1024;
      $("maxMb").textContent = h.max_upload_mb;
      const badge = $("modeBadge");
      badge.textContent = h.mode === "live" ? "Live" : "Demo mode";
      badge.className = `badge ${h.mode}`;
      $("modelBadge").textContent = h.mode === "live" ? `Model: ${h.gemma_model}` : "";
      $("demoBanner").hidden = h.mode !== "demo";
      if (h.missing_keys && h.missing_keys.length) {
        $("missingKeys").textContent = `Missing: ${h.missing_keys.join(", ")}.`;
      }
    } catch {
      $("modeBadge").textContent = "Server offline";
    }
  }

  async function loadPresets() {
    const res = await fetch("/api/presets");
    const presets = await res.json();
    const list = $("presetList");
    list.innerHTML = "";
    for (const p of presets) {
      const label = document.createElement("label");
      label.innerHTML = `<input type="checkbox" value="${p.id}" checked>
        <span>${p.label} <small>${p.width}x${p.height}</small></span>`;
      list.appendChild(label);
    }
  }

  function chooseFile(file) {
    if (!file) return;
    if (!ACCEPTED.includes(file.type)) {
      setStatus("Please choose a JPEG, PNG or WEBP image.", true);
      return;
    }
    if (file.size > state.maxBytes) {
      setStatus(`That image is larger than ${state.maxBytes / 1024 / 1024} MB.`, true);
      return;
    }
    state.file = file;
    const preview = $("previewImg");
    preview.src = URL.createObjectURL(file);
    preview.alt = `Preview of ${file.name}`;
    preview.hidden = false;
    $("dropText").hidden = true;
    processBtn.disabled = false;
    setStatus(`${file.name} (${formatBytes(file.size)}) ready.`);
  }

  fileInput.addEventListener("change", () => chooseFile(fileInput.files[0]));
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
  });
  ["dragenter", "dragover"].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.add("drag");
  }));
  ["dragleave", "drop"].forEach((ev) => dropzone.addEventListener(ev, (e) => {
    e.preventDefault(); dropzone.classList.remove("drag");
  }));
  dropzone.addEventListener("drop", (e) => chooseFile(e.dataTransfer.files[0]));

  document.querySelectorAll('input[name="bgMode"]').forEach((r) =>
    r.addEventListener("change", () => { $("brandColor").disabled = r.value !== "custom" || !r.checked; }));

  processBtn.addEventListener("click", async () => {
    if (!state.file) return;
    const form = new FormData();
    form.append("file", state.file);
    const custom = document.querySelector('input[name="bgMode"]:checked').value === "custom";
    form.append("brand_color", custom ? $("brandColor").value : "auto");
    const chosen = [...document.querySelectorAll("#presetList input:checked")].map((c) => c.value);
    form.append("presets", chosen.join(","));

    processBtn.disabled = true;
    setStatus("Gemma 4 is reading your photo and Cloudinary is preparing images...");
    try {
      const res = await fetch("/api/process", { method: "POST", body: form });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
      state.result = body;
      render(body);
      setStatus(`Done in ${(body.elapsed_ms / 1000).toFixed(1)} s.`);
    } catch (err) {
      setStatus(err.message, true);
    } finally {
      processBtn.disabled = false;
    }
  });

  function render(r) {
    $("results").hidden = false;
    renderStats(r);
    $("warnings").innerHTML = "";
    for (const w of r.warnings) {
      const div = document.createElement("div");
      div.className = "warning";
      div.textContent = w;
      $("warnings").appendChild(div);
    }
    renderListing(r.listing);
    renderCompare(r);
    renderVariants(r);
    $("results").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderStats(r) {
    const o = r.optimization || {};
    const saved = o.saved_percent != null ? `${o.saved_percent}%` : (r.mode === "demo" ? "Live only" : "n/a");
    const items = [
      [`${(r.elapsed_ms / 1000).toFixed(1)} s`, "Photo to listing"],
      [saved, "Bandwidth saved (f_auto, q_auto)"],
      [String(r.variants.length), "Channel-ready images"],
      [formatBytes(o.original_bytes), `Original${o.optimized_bytes ? `, now ${formatBytes(o.optimized_bytes)}` : ""}`],
    ];
    $("stats").innerHTML = "";
    for (const [value, label] of items) {
      const div = document.createElement("div");
      div.className = "stat";
      div.innerHTML = `<div class="value"></div><div class="label"></div>`;
      div.querySelector(".value").textContent = value;
      div.querySelector(".label").textContent = label;
      $("stats").appendChild(div);
    }
  }

  function renderListing(l) {
    $("listingCard").hidden = !l;
    if (!l) return;
    $("lCategory").textContent = l.category;
    $("lTitle").textContent = l.title;
    $("lDescription").textContent = l.description;
    $("lFeatures").innerHTML = "";
    l.features.forEach((f) => {
      const li = document.createElement("li");
      li.textContent = f;
      $("lFeatures").appendChild(li);
    });
    $("lTags").innerHTML = "";
    l.tags.forEach((t) => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = `#${t}`;
      $("lTags").appendChild(span);
    });
    $("lAlt").textContent = l.alt_text;
    $("lCaption").textContent = l.social_caption;
    $("lSwatch").style.background = l.background_hex;
    $("lHex").textContent = l.background_hex;
  }

  function cssColor(cloudinaryBg) {
    return cloudinaryBg && cloudinaryBg.startsWith("rgb:") ? `#${cloudinaryBg.slice(4)}` : "#f0f0f0";
  }

  function altFor(r, label) {
    const base = r.listing ? r.listing.alt_text : "Product photo";
    return `${base} (${label})`;
  }

  function renderCompare(r) {
    const after = r.variants.find((v) => v.id === "marketplace") || r.variants[0];
    $("beforeImg").src = r.original.url;
    $("beforeImg").alt = altFor(r, "original upload");
    $("afterImg").src = after.url;
    $("afterImg").alt = altFor(r, after.label);
    $("afterPane").style.background = cssColor(after.background_used);
    $("afterImg").style.width = r.mode === "demo" ? "70%" : "";
    updateCompare(50);
    $("compareRange").value = 50;
  }

  function updateCompare(value) {
    $("beforePane").style.clipPath = `inset(0 ${100 - value}% 0 0)`;
    $("compareHandle").style.left = `${value}%`;
  }
  $("compareRange").addEventListener("input", (e) => updateCompare(Number(e.target.value)));

  function loadWithRetry(img, frame, url, attempt = 0) {
    // Cloudinary may answer 423 while an AI transformation is still being generated.
    img.onload = () => frame.classList.add("ready");
    img.onerror = () => {
      if (attempt < 10) {
        setTimeout(() => loadWithRetry(img, frame, url, attempt + 1), 3000);
      } else {
        frame.classList.add("failed");
        frame.querySelector(".loading").textContent = "Could not generate. Open URL to retry.";
      }
    };
    img.src = attempt === 0 ? url : `${url}${url.includes("?") ? "&" : "?"}retry=${attempt}`;
  }

  function renderVariants(r) {
    const grid = $("variants");
    grid.innerHTML = "";
    const tpl = $("variantTpl");
    for (const v of r.variants) {
      const node = tpl.content.cloneNode(true);
      const frame = node.querySelector(".frame");
      const img = node.querySelector("img");
      frame.style.aspectRatio = `${v.width} / ${v.height}`;
      if (v.style === "cutout") frame.style.background = cssColor(v.background_used);
      if (r.mode === "demo") frame.classList.add("demo-render");
      img.alt = altFor(r, v.label);
      node.querySelector("h4").textContent = v.label;
      node.querySelector(".dims").textContent = `${v.width} x ${v.height}`;
      node.querySelector(".note").textContent = v.note;
      const dl = node.querySelector(".btn-small");
      dl.href = v.download_url;
      if (r.mode === "demo") dl.setAttribute("download", `snapshelf_${v.id}`);
      node.querySelector(".open").href = v.url;
      grid.appendChild(node);
      loadWithRetry(img, frame, v.url);
    }
  }

  async function copy(text, button) {
    try {
      await navigator.clipboard.writeText(text);
      const old = button.textContent;
      button.textContent = "copied";
      setTimeout(() => { button.textContent = old; }, 1200);
    } catch {
      setStatus("Copy failed. Select the text manually.", true);
    }
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-copy]");
    if (!btn || !state.result || !state.result.listing) return;
    const l = state.result.listing;
    const map = {
      alt: l.alt_text,
      caption: l.social_caption,
      all: [l.title, "", l.description, "", ...l.features.map((f) => `- ${f}`), "",
            l.tags.map((t) => `#${t.replace(/\s+/g, "")}`).join(" ")].join("\n"),
    };
    copy(map[btn.dataset.copy], btn);
  });

  loadHealth();
  loadPresets();
})();
