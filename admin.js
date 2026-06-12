const uploadForm = document.getElementById("uploadForm");
const uploadInput = document.getElementById("uploadInput");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");
const uploadList = document.getElementById("uploadList");
const uploadCount = document.getElementById("uploadCount");

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

loadUploads().catch((error) => {
  uploadStatus.textContent = error.message || "Could not load uploads.";
});
