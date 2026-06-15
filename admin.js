const uploadForm = document.getElementById("uploadForm");
const uploadInput = document.getElementById("uploadInput");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");
const uploadList = document.getElementById("uploadList");
const uploadCount = document.getElementById("uploadCount");
const manualRecordForm = document.getElementById("manualRecordForm");
const manualRecordButton = document.getElementById("manualRecordButton");
const manualRecordStatus = document.getElementById("manualRecordStatus");
const manualRecordList = document.getElementById("manualRecordList");
const manualRecordCount = document.getElementById("manualRecordCount");
const researchQueueForm = document.getElementById("researchQueueForm");
const researchQueueButton = document.getElementById("researchQueueButton");
const researchQueueStatus = document.getElementById("researchQueueStatus");

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function fileIcon(doc) {
  return doc.gallery_images && doc.gallery_images.length ? "Image" : "File";
}

function formObject(form) {
  const data = new FormData(form);
  const record = {};
  for (const [key, value] of data.entries()) {
    const clean = String(value || "").trim();
    if (clean) record[key] = clean;
  }
  return record;
}

function inferListingName(text, url) {
  const firstLine = String(text || "")
    .split(/\n+/)
    .map((line) => line.trim())
    .find(Boolean);
  if (firstLine) return firstLine.slice(0, 120);
  try {
    const parsed = new URL(url);
    return `${parsed.hostname.replace(/^www\./, "")} car wash lead`;
  } catch {
    return "New car wash research lead";
  }
}

async function postManualRecord(record) {
  const response = await fetch("/api/manual-records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ record }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Could not save record.");
  return data;
}

async function loadUploads() {
  const response = await fetch("/api/uploads", { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load uploads.");
  const data = await response.json();
  const uploads = Array.isArray(data.uploads) ? data.uploads : [];
  uploadCount.textContent = `${uploads.length.toLocaleString()} file${uploads.length === 1 ? "" : "s"}`;
  uploadList.innerHTML = uploads.length
    ? uploads
        .map(
          (doc) => `
            <article class="upload-row">
              <span>${escapeHtml(fileIcon(doc))}</span>
              <div>
                <strong>${escapeHtml(doc.title || doc.file_name)}</strong>
                <small>${escapeHtml(doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : "Uploaded file")}</small>
              </div>
              <a href="${escapeHtml(doc.pdf_url)}" target="_blank" rel="noreferrer">Open</a>
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">No admin uploads yet.</div>`;
}

async function loadManualRecords() {
  const response = await fetch("/api/manual-records", { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load added records.");
  const data = await response.json();
  const records = Array.isArray(data.records) ? data.records : [];
  manualRecordCount.textContent = `${records.length.toLocaleString()} record${records.length === 1 ? "" : "s"}`;
  manualRecordList.innerHTML = records.length
    ? records
        .slice(0, 80)
        .map(
          (record) => `
            <article class="upload-row">
              <span>${escapeHtml(/loopnet/i.test(record.source) ? "LN" : /bizbuysell/i.test(record.source) ? "BBS" : "Wash")}</span>
              <div>
                <strong>${escapeHtml(record.name || record.market || "Car wash record")}</strong>
                <small>${escapeHtml([record.market, record.state, record.asking_price, record.ebitda].filter(Boolean).join(" | ") || record.source || "Added record")}</small>
              </div>
              ${record.research_url ? `<a href="${escapeHtml(record.research_url)}" target="_blank" rel="noreferrer">Open</a>` : `<a href="/">Scout</a>`}
            </article>
          `
        )
        .join("")
    : `<div class="empty-state">No manually added washes yet.</div>`;
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = [...uploadInput.files];
  if (!files.length) {
    uploadStatus.textContent = "Choose at least one file first.";
    return;
  }

  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  uploadButton.disabled = true;
  uploadStatus.textContent = `Uploading ${files.length} file${files.length === 1 ? "" : "s"}...`;

  try {
    const response = await fetch("/api/uploads", { method: "POST", body });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Upload failed.");
    uploadInput.value = "";
    uploadStatus.textContent = "Upload complete. The files are now in the Document Library.";
    await loadUploads();
  } catch (error) {
    uploadStatus.textContent = error.message || "Upload failed.";
  } finally {
    uploadButton.disabled = false;
  }
});

if (manualRecordForm) {
  manualRecordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const record = formObject(manualRecordForm);
    if (!record.name && !record.market && !record.research_url && !record.note) {
      manualRecordStatus.textContent = "Add a name, address, URL, or note first.";
      return;
    }
    record.source = "Admin Added Listing";
    manualRecordButton.disabled = true;
    manualRecordStatus.textContent = "Saving to Scout...";
    try {
      await postManualRecord(record);
      manualRecordForm.reset();
      manualRecordStatus.textContent = "Saved. It will now appear in Scout search.";
      await loadManualRecords();
    } catch (error) {
      manualRecordStatus.textContent = error.message || "Could not save record.";
    } finally {
      manualRecordButton.disabled = false;
    }
  });
}

if (researchQueueForm) {
  researchQueueForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const record = formObject(researchQueueForm);
    if (!record.research_url && !record.full_text) {
      researchQueueStatus.textContent = "Paste a listing URL or listing text first.";
      return;
    }
    record.name = inferListingName(record.full_text, record.research_url);
    record.note = record.full_text || record.research_url;
    researchQueueButton.disabled = true;
    researchQueueStatus.textContent = "Saving research lead...";
    try {
      await postManualRecord(record);
      researchQueueForm.reset();
      researchQueueStatus.textContent = "Saved. The lead is now searchable in Scout.";
      await loadManualRecords();
    } catch (error) {
      researchQueueStatus.textContent = error.message || "Could not save research lead.";
    } finally {
      researchQueueButton.disabled = false;
    }
  });
}

loadUploads().catch((error) => {
  uploadStatus.textContent = error.message || "Could not load uploads.";
});
loadManualRecords().catch((error) => {
  if (manualRecordStatus) manualRecordStatus.textContent = error.message || "Could not load added records.";
});
