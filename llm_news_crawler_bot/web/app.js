const form = document.querySelector("#crawlForm");
const submitBtn = document.querySelector("#submitBtn");
const stopBtn = document.querySelector("#stopBtn");
const submitText = document.querySelector("#submitText");
const statusBadge = document.querySelector("#statusBadge");
const emptyState = document.querySelector("#emptyState");
const resultBody = document.querySelector("#resultBody");
const articleTitle = document.querySelector("#articleTitle");
const jobLink = document.querySelector("#jobLink");
const logsBox = document.querySelector("#logs");
const logCount = document.querySelector("#logCount");
let currentJobId = null;
let pollTimer = null;

const fields = {
  jobId: document.querySelector("#jobId"),
  sourceUrl: document.querySelector("#sourceUrl"),
  publishedAt: document.querySelector("#publishedAt"),
  author: document.querySelector("#author"),
  category: document.querySelector("#category"),
  tags: document.querySelector("#tags"),
  summary: document.querySelector("#summary"),
  content: document.querySelector("#content"),
  screenshot: document.querySelector("#screenshot"),
  itemsBar: document.querySelector("#itemsBar"),
  fileLinks: document.querySelector("#fileLinks"),
};

function setBusy(isBusy) {
  submitBtn.disabled = isBusy;
  stopBtn.disabled = !isBusy || !currentJobId;
  submitBtn.classList.toggle("loading", isBusy);
  submitText.textContent = isBusy ? "Dang crawl..." : "Bat dau crawl";
  statusBadge.textContent = isBusy ? "Running" : "Ready";
  statusBadge.className = isBusy ? "badge busy" : "badge";
}

function setError(message) {
  statusBadge.textContent = "Failed";
  statusBadge.className = "badge error";
  emptyState.hidden = false;
  resultBody.hidden = true;
  articleTitle.textContent = "Crawl that bai";
  emptyState.textContent = message;
}

function renderLogs(lines) {
  const safeLines = lines || [];
  logsBox.textContent = safeLines.length ? safeLines.join("\n") : "Waiting for job...";
  logCount.textContent = `${safeLines.length} lines`;
  logsBox.scrollTop = logsBox.scrollHeight;
}

function valueOrDash(value) {
  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "-";
  }
  return value || "-";
}

function renderItem(result, item) {
  const meta = item ? item.metadata : result.metadata;
  if (!meta) {
    setError("Khong co metadata tra ve.");
    return;
  }

  articleTitle.textContent = valueOrDash(meta.title);
  fields.jobId.textContent = result.job_id;
  fields.sourceUrl.textContent = valueOrDash(meta.source_url || meta.final_url);
  fields.publishedAt.textContent = valueOrDash(meta.published_at);
  fields.author.textContent = valueOrDash(meta.author);
  fields.category.textContent = valueOrDash(meta.category);
  fields.tags.textContent = valueOrDash(meta.tags);
  fields.summary.textContent = valueOrDash(meta.summary);
  fields.content.textContent = valueOrDash(meta.content);

  const index = item ? String(item.item_index).padStart(3, "0") : null;
  fields.screenshot.src = index
    ? `/output/${result.job_id}/items/item_${index}/screenshot.png?t=${Date.now()}`
    : `/output/${result.job_id}/screenshot.png?t=${Date.now()}`;
  fields.screenshot.hidden = false;

  const base = index ? `/output/${result.job_id}/items/item_${index}` : `/output/${result.job_id}`;
  fields.fileLinks.innerHTML = "";
  [
    ["Metadata JSON", `${base}/metadata.json`],
    ["Screenshot", `${base}/screenshot.png`],
    ["Content TXT", index ? `${base}/content.txt` : `${base}/article.txt`],
    ["Page HTML", `${base}/page.html`],
  ].forEach(([label, href]) => {
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = label;
    fields.fileLinks.appendChild(link);
  });
}

function renderItemsBar(result) {
  const items = result.items || [];
  fields.itemsBar.innerHTML = "";
  const aggregateLink = document.createElement("a");
  aggregateLink.href = `/output/${result.job_id}/metadata.json`;
  aggregateLink.target = "_blank";
  aggregateLink.rel = "noreferrer";
  aggregateLink.className = "itemTab";
  aggregateLink.textContent = "All metadata";
  fields.itemsBar.appendChild(aggregateLink);
  if (items.length <= 1) {
    return;
  }

  items.forEach((item, idx) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `itemTab${idx === 0 ? " active" : ""}`;
    button.textContent = `Item ${item.item_index}`;
    button.addEventListener("click", () => {
      document.querySelectorAll(".itemTab").forEach((el) => el.classList.remove("active"));
      button.classList.add("active");
      renderItem(result, item);
    });
    fields.itemsBar.appendChild(button);
  });
}

function renderResult(result) {
  const items = result.items || [];
  if (result.status !== "completed" || (!result.metadata && items.length === 0)) {
    setError(result.error || "Khong co metadata tra ve.");
    return;
  }

  statusBadge.textContent = "Done";
  statusBadge.className = "badge";
  emptyState.hidden = true;
  resultBody.hidden = false;

  renderItemsBar(result);
  renderItem(result, items[0] || null);
  jobLink.hidden = false;
  jobLink.href = `/api/jobs/${result.job_id}`;
}

async function pollJob(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Cannot read job");
  }

  renderLogs(data.logs);
  if (data.status === "completed" || data.status === "failed" || data.status === "stopped") {
    clearInterval(pollTimer);
    pollTimer = null;
    currentJobId = null;
    setBusy(false);

    if (data.status === "completed") {
      renderResult(data);
    } else {
      setError(data.error || `Job ${data.status}`);
    }
  } else {
    statusBadge.textContent = data.status || "Running";
    statusBadge.className = "badge busy";
  }
}

stopBtn.addEventListener("click", async () => {
  if (!currentJobId) return;
  stopBtn.disabled = true;
  await fetch(`/api/jobs/${currentJobId}/stop`, { method: "POST" });
  statusBadge.textContent = "Stopping";
  statusBadge.className = "badge busy";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (pollTimer) {
    clearInterval(pollTimer);
  }
  currentJobId = null;
  setBusy(true);
  emptyState.hidden = false;
  resultBody.hidden = true;
  jobLink.hidden = true;
  articleTitle.textContent = "Dang xu ly";
  emptyState.textContent = "Dang chay. Theo doi tien trinh trong Log monitor.";
  renderLogs(["Starting job..."]);

  const payload = {
    url: form.url.value.trim(),
    username: form.username.value.trim() || null,
    password: form.password.value || null,
    instruction: form.instruction.value.trim() || null,
    browser_mode: "auto",
    cdp_url: null,
    headless: true,
  };

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }
    currentJobId = data.job_id;
    stopBtn.disabled = false;
    fields.jobId.textContent = currentJobId;
    await pollJob(currentJobId);
    pollTimer = setInterval(() => {
      if (currentJobId) {
        pollJob(currentJobId).catch((error) => {
          clearInterval(pollTimer);
          pollTimer = null;
          currentJobId = null;
          setBusy(false);
          setError(error.message || String(error));
        });
      }
    }, 1000);
  } catch (error) {
    currentJobId = null;
    setError(error.message || String(error));
    setBusy(false);
  }
});
