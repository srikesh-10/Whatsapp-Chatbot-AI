const API_URL = "/verify";

const verifyForm = document.getElementById("verifyForm");
const claimInput = document.getElementById("claimInput");
const verifyButton = document.getElementById("verifyButton");
const demoButton = document.getElementById("demoButton");
const copyButton = document.getElementById("copyButton");
const statusText = document.getElementById("statusText");

const claimText = document.getElementById("claimText");
const verdictBadge = document.getElementById("verdictBadge");
const confidenceText = document.getElementById("confidenceText");
const sourcesList = document.getElementById("sourcesList");
const explanationText = document.getElementById("explanationText");
const counterMessage = document.getElementById("counterMessage");

let chart;
const verdictCounts = { true: 0, false: 0, uncertain: 0 };

function initChart() {
  const canvas = document.getElementById("verdictChart");
  if (!canvas || typeof Chart === "undefined") {
    return;
  }

  chart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: ["Likely True", "Likely False", "Uncertain"],
      datasets: [
        {
          data: [0, 0, 0],
          backgroundColor: ["#1f8f55", "#c4382f", "#b57a12"],
          borderColor: ["#ffffff", "#ffffff", "#ffffff"],
          borderWidth: 2,
          hoverOffset: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#3e4a43",
            boxWidth: 12,
            font: {
              family: "IBM Plex Sans",
            },
          },
        },
      },
    },
  });
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#b5332b" : "#5f6b63";
}

function normalizeVerdict(rawVerdict = "") {
  const value = String(rawVerdict).toLowerCase();

  if (value.includes("true")) {
    return { key: "true", text: "Likely True", className: "verdict-true" };
  }
  if (value.includes("false")) {
    return { key: "false", text: "Likely False", className: "verdict-false" };
  }
  if (value.includes("uncertain")) {
    return { key: "uncertain", text: "Uncertain", className: "verdict-uncertain" };
  }

  return { key: null, text: rawVerdict || "Unknown", className: "verdict-unknown" };
}

function updateSources(sources = []) {
  sourcesList.innerHTML = "";

  if (!Array.isArray(sources) || sources.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No sources returned by backend.";
    sourcesList.appendChild(li);
    return;
  }

  sources.forEach((source) => {
    const li = document.createElement("li");

    if (typeof source === "string" && source.startsWith("http")) {
      const anchor = document.createElement("a");
      anchor.href = source;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = source;
      li.appendChild(anchor);
    } else {
      li.textContent = String(source);
    }

    sourcesList.appendChild(li);
  });
}

function updateChart(verdictKey) {
  if (!chart || !verdictKey || !Object.prototype.hasOwnProperty.call(verdictCounts, verdictKey)) {
    return;
  }

  verdictCounts[verdictKey] += 1;
  chart.data.datasets[0].data = [
    verdictCounts.true,
    verdictCounts.false,
    verdictCounts.uncertain,
  ];
  chart.update();
}

function renderResult(result) {
  const claim = result?.claim || "No claim returned.";
  const confidence = Number.isFinite(Number(result?.confidence))
    ? Math.max(0, Math.min(100, Math.round(Number(result.confidence))))
    : 0;
  const explanation = result?.explanation || "No explanation returned.";
  const message = result?.counter_message || "No counter message returned.";

  const verdict = normalizeVerdict(result?.verdict);

  claimText.textContent = claim;
  verdictBadge.className = `verdict-badge ${verdict.className}`;
  verdictBadge.textContent = verdict.text;
  confidenceText.textContent = `${confidence}%`;
  explanationText.textContent = explanation;
  counterMessage.textContent = message;
  copyButton.disabled = false;

  updateSources(result?.sources || []);
  updateChart(verdict.key);
}

async function verifyClaim(claim) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ claim }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json();
}

verifyForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const claim = claimInput.value.trim();
  if (!claim) {
    setStatus("Please enter a claim before verifying.", true);
    return;
  }

  verifyButton.disabled = true;
  setStatus("Verifying claim against backend...");

  try {
    const result = await verifyClaim(claim);
    renderResult(result);
    setStatus("Verification complete.");
  } catch (error) {
    setStatus(`Verification failed: ${error.message}`, true);
  } finally {
    verifyButton.disabled = false;
  }
});

demoButton.addEventListener("click", () => {
  const demo = {
    claim: "Drinking turmeric cures diabetes",
    verdict: "LIKELY FALSE",
    confidence: 32,
    sources: ["WHO", "Healthline", "Wikipedia"],
    explanation:
      "The claim is likely misinformation because reliable medical sources do not support turmeric as a cure for diabetes.",
    counter_message:
      "FACT CHECK ALERT\n\nThe claim \"Drinking turmeric cures diabetes\" appears to be false.\nPlease verify information before sharing.",
  };

  renderResult(demo);
  setStatus("Loaded demo data.");
});

copyButton.addEventListener("click", async () => {
  const text = counterMessage.textContent.trim();
  if (!text || text === "Counter message will appear here.") {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("Counter message copied to clipboard.");
  } catch (error) {
    setStatus("Could not copy message. Please copy manually.", true);
  }
});

initChart();
