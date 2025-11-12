const apiBase = "/api/v1";
const storageKeys = {
  token: "ai-travel-token",
  user: "ai-travel-user",
};

const form = document.querySelector("[data-auth-form]");
if (!form) {
  if (window.location.search) {
    history.replaceState(null, "", window.location.pathname);
  }
} else {
  const mode = form.dataset.mode;
  const submitBtn = form.querySelector("[data-submit]");
  const statusEl = document.getElementById("formFeedback");
  const defaultButtonText = submitBtn?.textContent?.trim() ?? "";
  const fieldErrors = {};
  form.querySelectorAll("[data-error-for]").forEach((el) => {
    const key = el.dataset.errorFor;
    if (key) {
      fieldErrors[key] = el;
    }
  });

  const inputs = {
    email: form.querySelector('input[name="email"]'),
    password: form.querySelector('input[name="password"]'),
    confirm_password: form.querySelector('input[name="confirm_password"]'),
  };

  const flashMessage = form.dataset.flashMessage;
  const prefillEmail = form.dataset.prefillEmail;
  if (prefillEmail && inputs.email && !inputs.email.value) {
    inputs.email.value = prefillEmail;
  }
  if (flashMessage) {
    setStatus(flashMessage, "success");
    clearQueryString();
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!submitBtn) return;
    clearErrors();
    setStatus("");
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.email = (data.email || "").trim();
    let isValid = true;
    if (!data.email) {
      setFieldError("email", "请输入用户名或邮箱");
      isValid = false;
    }
    if (!data.password) {
      setFieldError("password", "请输入密码");
      isValid = false;
    } else if (String(data.password).length < 6) {
      setFieldError("password", "密码至少 6 位");
      isValid = false;
    }
    if (mode === "register") {
      if (!data.confirm_password) {
        setFieldError("confirm_password", "请再次输入密码");
        isValid = false;
      } else if (data.confirm_password !== data.password) {
        setFieldError("confirm_password", "两次密码输入不一致");
        isValid = false;
      }
    }
    if (!isValid) {
      setStatus("请检查表单后再提交", "error");
      return;
    }

    try {
      setLoading(true);
      if (mode === "login") {
        await handleLogin(data);
      } else {
        await handleRegister(data);
      }
    } catch (error) {
      console.error(error);
      if (mode === "login") {
        if (error?.status === 401) {
          setStatus("账号或密码错误", "error");
        } else {
          setStatus(error?.message || "登录失败，请稍后再试", "error");
        }
        if (inputs.password) {
          inputs.password.value = "";
          inputs.password.focus();
        }
      } else {
        const message = error?.message || "注册失败，请稍后再试";
        if (/邮箱|email/i.test(message)) {
          setFieldError("email", message);
        } else {
          setStatus(message, "error");
        }
      }
    } finally {
      setLoading(false);
    }
  });

  async function handleLogin(data) {
    const response = await fetch(`${apiBase}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: data.email, password: data.password }),
    });
    if (!response.ok) {
      const err = new Error(await parseError(response));
      err.status = response.status;
      throw err;
    }
    const payload = await response.json();
    window.localStorage.setItem(storageKeys.token, payload.access_token);
    window.localStorage.removeItem(storageKeys.user);
    setStatus("登录成功", "success");
    setTimeout(() => {
      window.location.href = "/app";
    }, 800);
  }

  async function handleRegister(data) {
    const response = await fetch(`${apiBase}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        full_name: data.email.split("@")[0],
      }),
    });
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    setStatus("注册成功，请登录", "success");
    setTimeout(() => {
      const params = new URLSearchParams({ registered: "1", email: data.email });
      window.location.href = `/login?${params.toString()}`;
    }, 800);
  }

  function setFieldError(field, message) {
    const el = fieldErrors[field];
    if (!el) return;
    el.textContent = message || "";
    el.classList.toggle("visible", Boolean(message));
  }

  function clearErrors() {
    Object.values(fieldErrors).forEach((el) => {
      el.textContent = "";
      el.classList.remove("visible");
    });
    setStatus("");
  }

  function setStatus(message, type = "info") {
    if (!statusEl) return;
    statusEl.textContent = message || "";
    statusEl.classList.remove("error", "success", "info");
    if (message) {
      statusEl.classList.add(type);
    }
  }

  function setLoading(isLoading) {
    if (!submitBtn) return;
    submitBtn.disabled = isLoading;
    submitBtn.setAttribute("aria-busy", String(isLoading));
    if (isLoading) {
      submitBtn.dataset.originalText = submitBtn.dataset.originalText || defaultButtonText;
      submitBtn.textContent = submitBtn.dataset.loadingText || "提交中...";
    } else if (submitBtn.dataset.originalText) {
      submitBtn.textContent = submitBtn.dataset.originalText;
    }
  }

  async function parseError(response) {
    try {
      const data = await response.json();
      if (Array.isArray(data.detail)) {
        return data.detail.map((item) => item.msg).join("；");
      }
      if (data.detail) return data.detail;
      if (data.message) return data.message;
    } catch {
      const text = await response.text();
      if (text) return text;
    }
    return response.status === 401 ? "账号或密码错误" : "请求失败，请稍后再试";
  }

  function clearQueryString() {
    if (window.location.search) {
      history.replaceState(null, "", window.location.pathname);
    }
  }
}
