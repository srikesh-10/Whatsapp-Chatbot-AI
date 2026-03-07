const API_URL = "/verify";

const verifyForm = document.getElementById("verifyForm");
const claimInput = document.getElementById("claimInput");
const verifyBtn = document.getElementById("verifyBtn");
const demoBtn = document.getElementById("demoBtn");
const copyBtn = document.getElementById("copyBtn");
const statusText = document.getElementById("statusText");

const claimText = document.getElementById("claimText");
const verdictText = document.getElementById("verdictText");
const confidenceText = document.getElementById("confidenceText");
const sourcesList = document.getElementById("sourcesList");
const explanationText = document.getElementById("explanationText");
const counterText = document.getElementById("counterText");

let chart;
const counts = { true: 0, false: 0, uncertain: 0 };

function initChart() {
  if (typeof Chart === "undefined") {
    return;
  }

  chart = new Chart(document.getElementById("verdictChart"), {
    type: "bar",
    data: {
      labels: ["True", "False", "Uncertain"],
      datasets: [
        {
          data: [0, 0, 0],
          backgroundColor: ["#1f8f55", "#be2d2d", "#b67c10"],
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
        },
      },
    },
  });
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#be2d2d" : "#5d6a60";
}

function normalizeVerdict(raw = "") {
  const verdict = String(raw).toLowerCase();
  if (verdict.includes("true")) {
    return { key: "true", label: "Likely True", className: "true" };
  }
  if (verdict.includes("false")) {
    return { key: "false", label: "Likely False", className: "false" };
  }
  if (verdict.includes("uncertain")) {
    return { key: "uncertain", label: "Uncertain", className: "uncertain" };
  }
  return { key: null, label: raw || "Unknown", className: "unknown" };
}

function renderSources(sources) {
  sourcesList.innerHTML = "";

  if (!Array.isArray(sources) || !sources.length) {
    const item = document.createElement("li");
    item.textContent = "No sources returned.";
    sourcesList.appendChild(item);
    return;
  }

  for (const source of sources) {
    const item = document.createElement("li");
    if (typeof source === "string" && source.startsWith("http")) {
      const anchor = document.createElement("a");
      anchor.href = source;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = source;
      item.appendChild(anchor);
    } else {
      item.textContent = String(source);
    }
    sourcesList.appendChild(item);
  }
}

function updateAnalytics(key) {
  if (!chart || !key || !(key in counts)) {
    return;
  }
  counts[key] += 1;
  chart.data.datasets[0].data = [counts.true, counts.false, counts.uncertain];
  chart.update();
}

function renderResult(data) {
  const normalized = normalizeVerdict(data.verdict);

  claimText.textContent = data.claim || "No claim returned.";
  verdictText.textContent = normalized.label;
  verdictText.className = `verdict ${normalized.className}`;
  confidenceText.textContent = `${Number(data.confidence || 0)}%`;
  explanationText.textContent = data.explanation || "No explanation returned.";
  counterText.textContent = data.counter_message || "No counter message returned.";

  copyBtn.disabled = false;
  renderSources(data.sources || []);
  updateAnalytics(normalized.key);
}

async function fetchVerification(claim) {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed with ${res.status}`);
  }

  return res.json();
}

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const claim = claimInput.value.trim();
  if (!claim) {
    setStatus("Please enter a claim.", true);
    return;
  }

  verifyBtn.disabled = true;
  setStatus("Running verification...");

  try {
    const result = await fetchVerification(claim);
    renderResult(result);
    setStatus("Verification completed.");
  } catch (error) {
    setStatus(`Verification failed: ${error.message}`, true);
  } finally {
    verifyBtn.disabled = false;
  }
});

demoBtn.addEventListener("click", () => {
  renderResult({
    claim: "Drinking turmeric cures diabetes",
    verdict: "LIKELY FALSE",
    confidence: 32,
    sources: ["WHO", "Healthline", "Wikipedia"],
    explanation:
      "The claim is likely misinformation because trusted medical sources do not support turmeric as a cure for diabetes.",
    counter_message:
      "FACT CHECK ALERT\n\nThe claim \"Drinking turmeric cures diabetes\" appears to be false.\nPlease verify information before sharing.",
  });
  setStatus("Loaded demo response.");
});

copyBtn.addEventListener("click", async () => {
  const text = counterText.textContent.trim();
  if (!text || text === "Counter message will appear here.") {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("Counter message copied.");
  } catch {
    setStatus("Copy failed. Please copy manually.", true);
  }
});

initChart();
