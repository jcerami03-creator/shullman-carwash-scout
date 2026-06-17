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
const screenshotLeadForm = document.getElementById("screenshotLeadForm");
const screenshotLeadInput = document.getElementById("screenshotLeadInput");
const screenshotLeadNote = document.getElementById("screenshotLeadNote");
const screenshotLeadButton = document.getElementById("screenshotLeadButton");
const screenshotLeadStatus = document.getElementById("screenshotLeadStatus");
let screenshotLeadFiles = [];
let uploadFilesPending = [];

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

async function uploadFiles(files) {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  const response = await fetch("/api/uploads", { method: "POST", body });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Upload failed.");
  return Array.isArray(data.uploads) ? data.uploads : [];
}

function fileSummary(files, singularLabel = "file") {
  if (!files.length) return "";
  if (files.length === 1) return `${files[0].name} ready.`;
  return `${files.length.toLocaleString()} ${singularLabel}s ready.`;
}

function setInputFiles(input, files) {
  try {
    const transfer = new DataTransfer();
    files.forEach((file) => transfer.items.add(file));
    input.files = transfer.files;
  } catch {
    // Some older browsers do not allow assigning file inputs. The saved file list is still used.
  }
}

function enableDropZone({ input, form, status, multiple = true, onFiles }) {
  const zone = form?.querySelector(".drop-zone");
  if (!zone || !input) return;

  input.addEventListener("change", () => {
    const files = [...input.files];
    onFiles(files);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, () => {
      zone.classList.remove("drag-over");
    });
  });

  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    const droppedFiles = [...(event.dataTransfer?.files || [])];
    if (!droppedFiles.length) return;
    const files = multiple ? droppedFiles : droppedFiles.slice(0, 1);
    setInputFiles(input, files);
    onFiles(files);
    if (status) status.textContent = fileSummary(files, "file");
  });
}

["dragover", "drop"].forEach((eventName) => {
  document.addEventListener(eventName, (event) => {
    if (event.dataTransfer?.types?.includes("Files")) event.preventDefault();
  });
});

enableDropZone({
  input: screenshotLeadInput,
  form: screenshotLeadForm,
  status: screenshotLeadStatus,
  multiple: false,
  onFiles(files) {
    screenshotLeadFiles = files;
    if (screenshotLeadStatus && files.length) {
      screenshotLeadStatus.textContent = `${fileSummary(files)} Add a link or note if you have one, then press Save Screenshot Lead.`;
    }
  },
});

enableDropZone({
  input: uploadInput,
  form: uploadForm,
  status: uploadStatus,
  multiple: true,
  onFiles(files) {
    uploadFilesPending = files;
    if (uploadStatus && files.length) {
      uploadStatus.textContent = `${fileSummary(files)} Press Upload Files to save them.`;
    }
  },
});

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
              <span>Wash</span>
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
  const files = uploadFilesPending.length ? uploadFilesPending : [...uploadInput.files];
  if (!files.length) {
    uploadStatus.textContent = "Choose at least one file first.";
    return;
  }

  uploadButton.disabled = true;
  uploadStatus.textContent = `Uploading ${files.length} file${files.length === 1 ? "" : "s"}...`;

  try {
    await uploadFiles(files);
    uploadFilesPending = [];
    uploadInput.value = "";
    uploadStatus.textContent = "Upload complete. The files are now in the Document Library.";
    await loadUploads();
  } catch (error) {
    uploadStatus.textContent = error.message || "Upload failed.";
  } finally {
    uploadButton.disabled = false;
  }
});

if (screenshotLeadForm) {
  screenshotLeadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const files = screenshotLeadFiles.length ? screenshotLeadFiles : [...screenshotLeadInput.files];
    const note = String(screenshotLeadNote.value || "").trim();
    if (!files.length) {
      screenshotLeadStatus.textContent = "Choose one screenshot or photo first.";
      return;
    }

    screenshotLeadButton.disabled = true;
    screenshotLeadStatus.textContent = "Analyzing and saving screenshot lead...";
    try {
      const uploads = await uploadFiles(files);
      const uploaded = uploads[0] || {};
      const fileName = uploaded.title || uploaded.file_name || files[0].name || "Screenshot lead";
      const noteIsUrl = /^https?:\/\//i.test(note);
      const record = {
        name: fileName.replace(/\.[^.]+$/, ""),
        market: noteIsUrl ? "" : note,
        note: [
          note,
          "Screenshot/photo lead uploaded from Admin. Review the linked image/PDF for full listing details.",
          uploaded.pdf_url ? `Uploaded file: ${uploaded.pdf_url}` : "",
        ]
          .filter(Boolean)
          .join(" "),
        research_url: noteIsUrl ? note : uploaded.pdf_url || "",
        uploaded_url: uploaded.pdf_url || "",
        source: "Screenshot Lead",
      };
      await postManualRecord(record);
      screenshotLeadFiles = [];
      screenshotLeadForm.reset();
      screenshotLeadStatus.textContent = "Saved. Screenshot and lead are now in Scout.";
      await loadUploads();
      await loadManualRecords();
    } catch (error) {
      screenshotLeadStatus.textContent = error.message || "Could not save screenshot lead.";
    } finally {
      screenshotLeadButton.disabled = false;
    }
  });
}

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

loadUploads().catch((error) => {
  uploadStatus.textContent = error.message || "Could not load uploads.";
});
loadManualRecords().catch((error) => {
  if (manualRecordStatus) manualRecordStatus.textContent = error.message || "Could not load added records.";
});
