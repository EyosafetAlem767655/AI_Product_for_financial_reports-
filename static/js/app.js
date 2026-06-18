function toNumber(value) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function asMoney(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

function calculateAge(value) {
  if (!value) return "";
  const dob = new Date(`${value}T00:00:00`);
  if (Number.isNaN(dob.getTime())) return "";
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDelta = today.getMonth() - dob.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age >= 0 ? String(age) : "";
}

function updateAgeFields() {
  document.querySelectorAll("[data-age-source]").forEach((input) => {
    const target = document.getElementById(input.dataset.ageSource);
    if (target) target.value = calculateAge(input.value);
  });
}

function updateSpousePanel() {
  const married = document.querySelector('input[name="marital_status"][value="married"]');
  const panel = document.querySelector(".spouse-panel");
  if (panel && married) {
    panel.classList.toggle("is-hidden", !married.checked);
  }
}

function resetRow(row) {
  row.querySelectorAll("input").forEach((input) => {
    input.value = "";
  });
  row.querySelectorAll("select").forEach((select) => {
    select.selectedIndex = 0;
  });
}

function bindDynamicRows() {
  document.addEventListener("click", (event) => {
    const addButton = event.target.closest("[data-add-row]");
    if (addButton) {
      const rowType = addButton.dataset.addRow;
      const container = document.querySelector(`[data-row-container="${rowType}"]`);
      const source = container ? container.querySelector(`[data-row="${rowType}"]:last-child`) : null;
      if (container && source) {
        const clone = source.cloneNode(true);
        resetRow(clone);
        container.appendChild(clone);
      }
    }

    const removeButton = event.target.closest("[data-remove-row]");
    if (removeButton) {
      const row = removeButton.closest("[data-row]");
      const container = row ? row.parentElement : null;
      if (row && container && container.children.length > 1) {
        row.remove();
      } else if (row) {
        resetRow(row);
      }
    }

    const useLast = event.target.closest(".use-last");
    if (useLast) {
      const target = document.getElementById(useLast.dataset.target);
      if (target) {
        target.value = useLast.dataset.value;
        target.dispatchEvent(new Event("input", { bubbles: true }));
      }
    }
  });
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = asMoney(value);
}

function recalculateReport() {
  const form = document.getElementById("report-form");
  if (!form) return;
  const inflow = toNumber(document.getElementById("inflow")?.value);
  const outflow = toNumber(document.getElementById("outflow")?.value);
  const propertyValue = toNumber(document.getElementById("property_value")?.value);
  const deductibleTotal = Array.from(document.querySelectorAll(".deductible-input"))
    .reduce((sum, input) => sum + toNumber(input.value), 0);

  let client1 = 0;
  let client2 = 0;
  let nonRetirement = 0;
  document.querySelectorAll("[data-account-row]").forEach((row) => {
    const balance = toNumber(row.querySelector(".account-balance")?.value);
    if (row.dataset.category === "retirement" && row.dataset.owner === "client1") {
      client1 += balance;
    } else if (row.dataset.category === "retirement" && row.dataset.owner === "client2") {
      client2 += balance;
    } else if (row.dataset.category === "non_retirement") {
      nonRetirement += balance;
    }
  });

  const liabilityTotal = Array.from(document.querySelectorAll(".liability-balance"))
    .reduce((sum, input) => sum + toNumber(input.value), 0);

  setText("calc-excess", inflow - outflow);
  setText("calc-reserve-target", (outflow * 6) + deductibleTotal);
  setText("calc-client1", client1);
  setText("calc-client2", client2);
  setText("calc-non-retirement", nonRetirement);
  setText("calc-grand", client1 + client2 + nonRetirement + propertyValue);
  setText("calc-liabilities", liabilityTotal);
}

function bindReportForm() {
  const form = document.getElementById("report-form");
  if (!form) return;
  form.addEventListener("input", (event) => {
    const missingWrapper = event.target.closest(".missing");
    if (missingWrapper && event.target.value.trim() !== "") {
      missingWrapper.classList.remove("missing");
    }
    recalculateReport();
  });
  recalculateReport();
}

document.addEventListener("DOMContentLoaded", () => {
  updateAgeFields();
  updateSpousePanel();
  document.querySelectorAll("[data-age-source]").forEach((input) => {
    input.addEventListener("input", updateAgeFields);
  });
  document.querySelectorAll('input[name="marital_status"]').forEach((input) => {
    input.addEventListener("change", updateSpousePanel);
  });
  bindDynamicRows();
  bindReportForm();
});
