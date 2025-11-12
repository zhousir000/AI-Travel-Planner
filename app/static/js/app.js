const apiBase = "/api/v1";
const storageKeys = {
  token: "ai-travel-token",
  user: "ai-travel-user",
  settings: "ai-travel-client-settings",
};

const state = {
  token: window.localStorage.getItem(storageKeys.token) || null,
  user: null,
  plans: [],
  currentPlanId: null,
  map: null,
  markers: [],
  authMode: "login",
};

const dom = {
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  logoutBtn: document.getElementById("logoutBtn"),
  plannerForm: document.getElementById("plannerForm"),
  voiceBtn: document.getElementById("voiceBtn"),
  voiceStatus: document.getElementById("voiceStatus"),
  plannerFeedback: document.getElementById("plannerFeedback"),
  planList: document.getElementById("planList"),
  planDetailsSection: document.getElementById("planDetailsSection"),
  planTitle: document.getElementById("planTitle"),
  planMeta: document.getElementById("planMeta"),
  planBudget: document.getElementById("planBudget"),
  itineraryTimeline: document.getElementById("itineraryTimeline"),
  mapContainer: document.getElementById("mapContainer"),
  mapHint: document.getElementById("mapHint"),
  expenseForm: document.getElementById("expenseForm"),
  expenseList: document.getElementById("expenseList"),
  expenseTotal: document.getElementById("expenseTotal"),
  clientSettingsForm: document.getElementById("clientSettingsForm"),
  clearSettingsBtn: document.getElementById("clearSettingsBtn"),
  settingsFeedback: document.getElementById("settingsFeedback"),
  authStatus: document.getElementById("authStatus"),
  goToRegisterBtn: document.getElementById("goToRegisterBtn"),
  goToLoginBtn: document.getElementById("goToLoginBtn"),
};

async function apiFetch(path, { method = "GET", headers = {}, body } = {}) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (state.token) {
    opts.headers.Authorization = `Bearer ${state.token}`;
  }

  if (body instanceof FormData) {
    delete opts.headers["Content-Type"];
    opts.body = body;
  } else if (body !== undefined) {
    opts.body = JSON.stringify(body);
  }

  const response = await fetch(`${apiBase}${path}`, opts);
  if (response.status === 401) {
    handleLogout();
    throw new Error("请重新登录");
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function setToken(token) {
  state.token = token;
  if (token) {
    window.localStorage.setItem(storageKeys.token, token);
  } else {
    window.localStorage.removeItem(storageKeys.token);
  }
}

function showFeedback(el, message, type = "info") {
  if (!el) return;
  el.textContent = message;
  el.classList.remove("error", "success");
  if (type === "error") el.classList.add("error");
  if (type === "success") el.classList.add("success");
}

function setAuthMode(mode) {
  state.authMode = mode;
  const showLogin = mode === "login";
  if (dom.loginForm) {
    dom.loginForm.classList.toggle("hidden", !showLogin);
  }
  if (dom.registerForm) {
    dom.registerForm.classList.toggle("hidden", showLogin);
  }
}

function updateAuthStatus() {
  if (!dom.authStatus) return;
  if (state.user) {
    const name = state.user.full_name || state.user.email || "已登录用户";
    dom.authStatus.textContent = `当前已登录：${name}`;
  } else {
    dom.authStatus.textContent = "当前未登录";
  }
}

async function handleLogin(event) {
  event?.preventDefault();
  const formData = new FormData(dom.loginForm);
  try {
    const result = await apiFetch("/auth/login", {
      method: "POST",
      body: {
        email: formData.get("email"),
        password: formData.get("password"),
      },
    });
    setToken(result.access_token);
    showFeedback(dom.plannerFeedback, "登录成功，正在加载行程...", "success");
    await fetchCurrentUser();
    await loadPlans();
    updateAuthStatus();
  } catch (error) {
    showFeedback(dom.plannerFeedback, `登录失败：${error.message}`, "error");
  }
}

async function handleRegister(event) {
  event?.preventDefault();
  const formData = new FormData(dom.registerForm);
  try {
    await apiFetch("/auth/register", {
      method: "POST",
      body: {
        full_name: formData.get("full_name") || null,
        email: formData.get("email"),
        password: formData.get("password"),
      },
    });
    showFeedback(dom.plannerFeedback, "注册成功，请直接登录。", "success");
    setAuthMode("login");
  } catch (error) {
    showFeedback(dom.plannerFeedback, `注册失败：${error.message}`, "error");
  }
}

function handleLogout() {
  setToken(null);
  state.user = null;
  window.localStorage.removeItem(storageKeys.user);
  state.plans = [];
  state.currentPlanId = null;
  renderPlanList();
  renderPlanDetails(null);
  showFeedback(dom.plannerFeedback, "已退出登录。");
  updateAuthStatus();
  window.location.href = "/login";
}

async function fetchCurrentUser() {
  if (!state.token) {
    updateAuthStatus();
    return;
  }
  try {
    const user = await apiFetch("/users/me");
    state.user = user;
    window.localStorage.setItem(storageKeys.user, JSON.stringify(user));
  } catch (error) {
    console.error(error);
  }
  updateAuthStatus();
}

function getFormValues(form) {
  const formData = new FormData(form);
  return Object.fromEntries(formData.entries());
}

async function handleGeneratePlan(event) {
  event?.preventDefault();
  if (!state.token) {
    showFeedback(dom.plannerFeedback, "请先登录再生成行程。", "error");
    return;
  }
  const values = getFormValues(dom.plannerForm);
  const payload = {
    destination: values.destination,
    start_date: values.start_date || null,
    end_date: values.end_date || null,
    duration_days: values.duration_days ? Number(values.duration_days) : null,
    travelers: values.travelers ? Number(values.travelers) : null,
    budget_amount: values.budget_amount ? Number(values.budget_amount) : null,
    currency: "CNY",
    interests: values.interests || "",
    travel_style: values.travel_style || "",
    notes: values.notes || null,
  };
  const clientSettings = loadClientSettings();
  if (clientSettings.llmProvider) {
    payload.llm_provider = clientSettings.llmProvider;
  }
  if (clientSettings.llmApiKey) {
    payload.llm_api_key = clientSettings.llmApiKey;
  }
  if (clientSettings.llmEndpoint) {
    payload.llm_endpoint = clientSettings.llmEndpoint;
  }
  if (!payload.destination) {
    showFeedback(dom.plannerFeedback, "请输入旅行目的地。", "error");
    return;
  }
  showFeedback(dom.plannerFeedback, "正在生成行程，请稍候...");
  try {
    const response = await apiFetch("/plans/generate", {
      method: "POST",
      body: payload,
    });
    const plan = response.plan;
    state.plans.unshift(plan);
    state.currentPlanId = plan.id;
    renderPlanList();
    renderPlanDetails(plan);
    showFeedback(dom.plannerFeedback, "生成成功，行程已保存。", "success");
  } catch (error) {
    showFeedback(dom.plannerFeedback, `生成失败：${error.message}`, "error");
  }
}

async function loadPlans() {
  if (!state.token) return;
  try {
    const plans = await apiFetch("/plans");
    state.plans = plans;
    if (plans.length > 0) {
      state.currentPlanId = plans[0].id;
      renderPlanDetails(plans[0]);
    } else {
      renderPlanDetails(null);
    }
    renderPlanList();
  } catch (error) {
    console.error(error);
  }
}

function renderPlanList() {
  if (!dom.planList) return;
  dom.planList.innerHTML = "";
  state.plans.forEach((plan) => {
    const li = document.createElement("li");
    li.className = "plan-card" + (plan.id === state.currentPlanId ? " active" : "");
    li.innerHTML = `
      <h4>${plan.title}</h4>
      <p class="muted small">${plan.destination}</p>
      <p class="muted small">${formatPlanDates(plan)}</p>
    `;
    li.addEventListener("click", async () => {
      state.currentPlanId = plan.id;
      renderPlanList();
      if (!plan.itinerary || !plan.itinerary.days) {
        const latest = await apiFetch(`/plans/${plan.id}`);
        updatePlanInState(latest);
        renderPlanDetails(latest);
      } else {
        renderPlanDetails(plan);
      }
    });
    dom.planList.appendChild(li);
  });
}

function updatePlanInState(updatedPlan) {
  const index = state.plans.findIndex((p) => p.id === updatedPlan.id);
  if (index >= 0) {
    state.plans[index] = updatedPlan;
  } else {
    state.plans.unshift(updatedPlan);
  }
}

function renderPlanDetails(plan) {
  if (!dom.planDetailsSection) return;
  if (!plan) {
    dom.planDetailsSection.classList.add("hidden");
    return;
  }
  dom.planDetailsSection.classList.remove("hidden");
  dom.planTitle.textContent = plan.title;
  dom.planMeta.textContent = `${plan.destination} · ${formatPlanDates(plan)}`;
  const budget = plan.budget_breakdown?.summary;
  if (budget) {
    dom.planBudget.textContent = `预算：${budget.total ?? "—"} ${budget.currency ?? ""}`;
  } else {
    dom.planBudget.textContent = "预算：--";
  }
  renderItinerary(plan.itinerary, plan.currency);
  renderExpenses(plan);
  renderMap(plan.itinerary);
}

function formatPlanDates(plan) {
  const start = plan.start_date ? new Date(plan.start_date).toLocaleDateString() : "待定";
  const end = plan.end_date ? new Date(plan.end_date).toLocaleDateString() : "";
  return end ? `${start} - ${end}` : start;
}

function renderItinerary(itinerary, currency) {
  if (!dom.itineraryTimeline) return;
  dom.itineraryTimeline.innerHTML = "";
  const days = itinerary?.days || [];
  const planCurrency = currency || "CNY";
  days.forEach((day) => {
    const wrapper = document.createElement("div");
    wrapper.className = "timeline-day";
    const dayTitle = document.createElement("h4");
    const dateText = day.date ? new Date(day.date).toLocaleDateString() : "";
    dayTitle.textContent = `第 ${day.day || day.day_index} 天 · ${day.headline || ""} ${dateText}`;
    wrapper.appendChild(dayTitle);
    const activities = day.activities || [];
    activities.forEach((act) => {
      const row = document.createElement("div");
      row.className = "timeline-activity";
      const costText = formatMoney(act.estimated_cost, planCurrency);
      row.innerHTML = `
        <strong>${act.time || ""} ${act.title}</strong>
        <p class="muted small">${act.description || ""}</p>
        ${act.location ? `<p class="small">📍 ${act.location}</p>` : ""}
        ${costText ? `<span class="cost-chip">约 ${costText}</span>` : ""}
      `;
      wrapper.appendChild(row);
    });
    dom.itineraryTimeline.appendChild(wrapper);
  });
}

function formatMoney(value, currency) {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return null;
  }
  const currencyLabel = currency || "CNY";
  const formatted = amount % 1 === 0 ? amount.toFixed(0) : amount.toFixed(2);
  return `${formatted} ${currencyLabel}`;
}

function renderExpenses(plan) {
  if (!dom.expenseList) return;
  dom.expenseList.innerHTML = "";
  const expenses = plan.expenses || [];
  let total = 0;
  expenses.forEach((exp) => {
    total += Number(exp.amount);
    const li = document.createElement("li");
    li.className = "expense-item";
    li.innerHTML = `
      <div>
        <strong>${exp.category}</strong>
        <p class="muted small">${exp.note || ""}</p>
      </div>
      <div>
        <span>${Number(exp.amount).toFixed(2)} ${exp.currency || ""}</span>
      </div>
    `;
    dom.expenseList.appendChild(li);
  });
  dom.expenseTotal.textContent = `当前记录：¥${total.toFixed(2)}`;
}

async function refreshExpenses() {
  if (!state.currentPlanId) return;
  const plan = await apiFetch(`/plans/${state.currentPlanId}`);
  updatePlanInState(plan);
  renderPlanDetails(plan);
}

function tryInitMap() {
  if (!dom.mapContainer || !window.AMap) {
    dom.mapHint.textContent = "地图尚未加载，请在设置中填写高德地图 Key。";
    return;
  }
  dom.mapHint.textContent = "";
  state.map = new window.AMap.Map("mapContainer", {
    zoom: 12,
    viewMode: "3D",
  });
}

function renderMap(itinerary) {
  if (!dom.mapContainer) return;
  if (!window.AMap) {
    dom.mapHint.textContent = "未检测到高德地图脚本。";
    return;
  }
  if (!state.map) {
    tryInitMap();
  }
  if (!state.map) return;
  state.map.clearMap();
  const coords = [];
  const days = itinerary?.days || [];
  days.forEach((day) => {
    (day.activities || []).forEach((act) => {
      if (act.latitude && act.longitude) {
        const marker = new window.AMap.Marker({
          position: [act.longitude, act.latitude],
          title: act.title,
        });
        marker.setMap(state.map);
        coords.push([act.longitude, act.latitude]);
      }
    });
  });
  if (coords.length > 0) {
    state.map.setFitView();
  } else {
    dom.mapHint.textContent = "行程中暂无坐标信息，可在设置中配置地理编码。";
  }
}

async function handleAddExpense(event) {
  event?.preventDefault();
  if (!state.currentPlanId) {
    showFeedback(dom.plannerFeedback, "请先选择行程。", "error");
    return;
  }
  const formData = new FormData(dom.expenseForm);
  const payload = {
    category: formData.get("category"),
    amount: Number(formData.get("amount")),
    currency: "CNY",
    note: formData.get("note") || null,
  };
  try {
    await apiFetch(`/plans/${state.currentPlanId}/expenses`, {
      method: "POST",
      body: payload,
    });
    dom.expenseForm.reset();
    await refreshExpenses();
  } catch (error) {
    showFeedback(dom.plannerFeedback, `添加费用失败：${error.message}`, "error");
  }
}

function initVoiceRecognition() {
  if (!dom.voiceBtn) return;
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    dom.voiceStatus.textContent = "浏览器不支持 Web Speech API，可在设置页切换到科大讯飞。";
    dom.voiceBtn.addEventListener("click", () => {
      alert("当前浏览器不支持原生语音识别，请尝试在设置中配置科大讯飞 Key。");
    });
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onstart = () => {
    dom.voiceStatus.textContent = "正在聆听...";
    dom.voiceBtn.disabled = true;
  };
  recognition.onerror = (event) => {
    dom.voiceStatus.textContent = `语音识别失败：${event.error}`;
    dom.voiceBtn.disabled = false;
  };
  recognition.onend = () => {
    dom.voiceBtn.disabled = false;
  };
  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    dom.voiceStatus.textContent = `识别结果：${transcript}`;
    dom.plannerForm.elements["notes"].value = `${dom.plannerForm.elements["notes"].value}\n${transcript}`.trim();
    if (window.appConfig?.speechProvider === "iflytek") {
      await sendVoiceTranscript(transcript);
    }
  };
  dom.voiceBtn.addEventListener("click", () => recognition.start());
}

async function sendVoiceTranscript(transcript) {
  try {
    const body = new FormData();
    body.append("transcript_text", transcript);
    const response = await apiFetch("/speech/transcribe", {
      method: "POST",
      headers: {},
      body,
    });
    if (response?.transcript) {
      dom.voiceStatus.textContent = `后端复核：${response.transcript}`;
    }
  } catch (error) {
    console.warn("Speech backend error:", error.message);
  }
}

function hydrateFromStorage() {
  if (!state.token) {
    state.user = null;
    window.localStorage.removeItem(storageKeys.user);
    return;
  }
  const userRaw = window.localStorage.getItem(storageKeys.user);
  if (userRaw) {
    try {
      state.user = JSON.parse(userRaw);
    } catch (error) {
      console.warn("Failed to parse user cache:", error);
    }
  }
}

function initEventListeners() {
  dom.loginForm?.addEventListener("submit", handleLogin);
  dom.registerForm?.addEventListener("submit", handleRegister);
  dom.logoutBtn?.addEventListener("click", handleLogout);
  dom.plannerForm?.addEventListener("submit", handleGeneratePlan);
  dom.expenseForm?.addEventListener("submit", handleAddExpense);
  dom.clientSettingsForm?.addEventListener("submit", handleSaveSettings);
  dom.clearSettingsBtn?.addEventListener("click", clearSettings);
  dom.goToRegisterBtn?.addEventListener("click", () => setAuthMode("register"));
  dom.goToLoginBtn?.addEventListener("click", () => setAuthMode("login"));
}

async function bootstrap() {
  hydrateFromStorage();
  hydrateSettings();
  setAuthMode(state.authMode);
  updateAuthStatus();
  initEventListeners();
  initVoiceRecognition();
  if (state.token) {
    await fetchCurrentUser();
    await loadPlans();
  }
  if (window.AMap) {
    tryInitMap();
  } else {
    window.addEventListener("load", tryInitMap);
  }
}

bootstrap();

function loadClientSettings() {
  const saved = window.localStorage.getItem(storageKeys.settings);
  if (!saved) return {};
  try {
    const data = JSON.parse(saved);
    if (data && typeof data === "object") {
      return data;
    }
  } catch (error) {
    console.warn("Failed to load client settings", error);
  }
  return {};
}

function hydrateSettings() {
  if (!dom.clientSettingsForm) return;
  const data = loadClientSettings();
  for (const [key, value] of Object.entries(data)) {
    const field = dom.clientSettingsForm.elements[key];
    if (field) {
      field.value = value;
    }
  }
}

function collectSettingsForm() {
  if (!dom.clientSettingsForm) return {};
  const formData = new FormData(dom.clientSettingsForm);
  return Object.fromEntries(formData.entries());
}

function clearSettings() {
  if (!dom.clientSettingsForm) return;
  dom.clientSettingsForm.reset();
  window.localStorage.removeItem(storageKeys.settings);
  showFeedback(dom.settingsFeedback, "已清除客户端设置。", "success");
}

function handleSaveSettings(event) {
  event?.preventDefault();
  if (!dom.clientSettingsForm) return;
  const payload = collectSettingsForm();
  window.localStorage.setItem(storageKeys.settings, JSON.stringify(payload));
  showFeedback(dom.settingsFeedback, "设置已保存，仅保存在本地浏览器。", "success");
}
