(function () {
  const $ = (selector) => document.querySelector(selector);
  const apiInput = $("#apiUrl");
  const saveBtn = $("#saveApi");
  const apiStatus = $("#apiStatus");
  const form = $("#predictForm");
  const formMessage = $("#formMessage");
  const resultBox = $("#result");
  const resultContent = $("#resultContent");

  const qp = new URLSearchParams(window.location.search);
  const qsApi = qp.get("api");
  const lsApi = localStorage.getItem("apiBaseUrl");
  apiInput.value = qsApi || lsApi || "http://localhost:8000";

  saveBtn.addEventListener("click", () => {
    localStorage.setItem("apiBaseUrl", apiInput.value.trim());
    apiStatus.textContent = "Alamat tersimpan.";
    setTimeout(() => (apiStatus.textContent = ""), 1500);
  });

  const selectWithOther = document.querySelectorAll("[data-other-target]");
  selectWithOther.forEach((select) => {
    const wrap = document.querySelector(select.dataset.otherTarget);
    if (!wrap) return;
    const input = wrap.querySelector("input");
    const toggle = () => {
      if (select.value === "OTHER") {
        wrap.classList.remove("hidden");
        if (input) input.focus();
      } else {
        wrap.classList.add("hidden");
        if (input) input.value = "";
      }
    };
    select.addEventListener("change", toggle);
    toggle();
  });

  const fieldConfigs = [
    {
      key: "FULL_TIME_POSITION",
      select: "#fullTimeSelect",
      other: "#fullTimeOther",
      transform: (value) => value.trim().toUpperCase(),
      label: "Status kerja utama",
    },
    {
      key: "EMPLOYER_STATE",
      select: "#employerStateSelect",
      other: "#employerStateOther",
      transform: (value) => value.trim().toUpperCase(),
      label: "Lokasi kantor pemberi kerja",
    },
    {
      key: "WORKSITE_STATE",
      select: "#worksiteStateSelect",
      other: "#worksiteStateOther",
      transform: (value) => value.trim().toUpperCase(),
      label: "Lokasi tempat bekerja",
    },
    {
      key: "SOC_CODE",
      select: "#socSelect",
      other: "#socOther",
      transform: (value) => value.trim(),
      label: "Kode jabatan (SOC)",
    },
    {
      key: "WAGE_RATE",
      select: "#wageSelect",
      other: "#wageOther",
      transform: (value) => {
        const num = Number(value);
        return Number.isFinite(num) ? num : NaN;
      },
      label: "Perkiraan gaji tahunan",
      isNumeric: true,
    },
  ];

  function gatherPayload() {
    const payload = {};
    const errors = [];

    fieldConfigs.forEach((cfg) => {
      const select = $(cfg.select);
      const otherInput = cfg.other ? $(cfg.other) : null;
      if (!select) return;
      select.classList.remove("error");
      if (otherInput) otherInput.classList.remove("error");

      const usesOther = select.value === "OTHER";
      let raw = usesOther ? (otherInput ? otherInput.value : "") : select.value;
      raw = raw != null ? String(raw).trim() : "";

      if (!raw) {
        errors.push(`${cfg.label} belum diisi.`);
        (usesOther && otherInput ? otherInput : select).classList.add("error");
        return;
      }

      let transformed = cfg.transform ? cfg.transform(raw) : raw;

      if (cfg.isNumeric) {
        if (!Number.isFinite(transformed) || transformed <= 0) {
          errors.push(`${cfg.label} harus berupa angka positif.`);
          (usesOther && otherInput ? otherInput : select).classList.add("error");
          return;
        }
      }

      payload[cfg.key] = transformed;
    });

    return { payload, errors };
  }

  function showFormMessage(message, type) {
    if (!message) {
      formMessage.textContent = "";
      formMessage.classList.add("hidden");
      formMessage.classList.remove("error", "success");
      return;
    }
    formMessage.textContent = message;
    formMessage.classList.remove("hidden");
    formMessage.classList.toggle("error", type === "error");
    formMessage.classList.toggle("success", type === "success");
  }

  function renderResult(data) {
    let cardHtml = "";

    if (data.error) {
      cardHtml = `
        <div class="result-card warning">
          <div class="badge">Terjadi Kesalahan</div>
          <p>${data.error}</p>
        </div>
      `;
    } else {
      const label = data.label || "Tidak diketahui";
      const probability =
        typeof data.proba_certified === "number"
          ? Math.round(data.proba_certified * 1000) / 10
          : null;
      const isApproved = label === "CERTIFIED";
      const statusText = isApproved
        ? "Kemungkinan disetujui"
        : label === "DENIED"
        ? "Kemungkinan ditolak"
        : "Status tidak dikenal";
      const description = isApproved
        ? "Model memperkirakan permohonan Anda akan disetujui."
        : label === "DENIED"
        ? "Model memperkirakan permohonan Anda akan ditolak."
        : "Model tidak dapat menentukan hasil secara pasti.";
      const badgeClass = isApproved ? "positive" : label === "DENIED" ? "negative" : "neutral";
      const probText =
        probability != null
          ? `${probability}% peluang disetujui`
          : "Probabilitas tidak tersedia.";

      cardHtml = `
        <div class="result-card ${badgeClass}">
          <div class="badge">${statusText}</div>
          <p>${description}</p>
          <p class="probability">${probText}</p>
        </div>
      `;

      cardHtml += `
        <details class="raw-details">
          <summary>Lihat detail respons</summary>
          <pre>${JSON.stringify(data, null, 2)}</pre>
        </details>
      `;
    }

    resultContent.innerHTML = cardHtml.trim();
    resultBox.classList.remove("hidden");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showFormMessage("", "");
    resultBox.classList.add("hidden");

    const base = apiInput.value.trim().replace(/\/$/, "");
    if (!base) {
      showFormMessage("Isi terlebih dahulu alamat API.", "error");
      return;
    }

    const { payload, errors } = gatherPayload();
    if (errors.length > 0) {
      showFormMessage(errors.join(" "), "error");
      return;
    }

    try {
      const response = await fetch(`${base}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      renderResult(data);
    } catch (error) {
      renderResult({ error: String(error) });
    }
  });
})();
