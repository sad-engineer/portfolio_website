(function () {
  const form = document.getElementById("feedback-form");
  if (!form) {
    return;
  }

  const submitButton = form.querySelector(".feedback__submit");
  const formTitleEl = form.querySelector("h2");
  const contactInputEl = form.querySelector('input[name="phone"]');
  const contactInputLabelEl = form.querySelector('label[for="phone"]');
  const consentFieldEl = form.querySelector(".consent");
  const consentCheckboxEl = form.querySelector('input[name="consent"]');
  const turnstileMountEl = form.querySelector("#feedback-turnstile");
  const statusEl = document.getElementById("feedback-form-status");
  const endpoint = form.dataset.feedbackEndpoint || "/api/feedback";
  const lang = form.dataset.feedbackLang || "ru";
  const page = form.dataset.feedbackPage || window.location.pathname;
  const turnstileSiteKey = String(form.dataset.turnstileSiteKey || "").trim();

  const defaultSubmitText =
    form.dataset.msgSubmitDefault || submitButton?.textContent?.trim() || "Отправить";
  const callSubmitText = form.dataset.msgSubmitCall || defaultSubmitText;
  const messageSubmitText = form.dataset.msgSubmitMessage || defaultSubmitText;
  const callFormTitle = form.dataset.formTitleCall || formTitleEl?.textContent?.trim() || "";
  const messageFormTitle = form.dataset.formTitleMessage || callFormTitle;
  const phoneInputLabel = form.dataset.inputLabelPhone || "Ваш номер";
  const phoneInputPlaceholder = form.dataset.inputPlaceholderPhone || "+7 (___) ___-__-__";
  const emailInputLabel = form.dataset.inputLabelEmail || "Ваш email";
  const emailInputPlaceholder = form.dataset.inputPlaceholderEmail || "пример емейла";
  const sendingText = form.dataset.msgSubmitSending || "Отправка...";
  const validationErrorText =
    form.dataset.msgValidationError || "Проверьте заполнение формы.";
  const requestErrorText =
    form.dataset.msgRequestError || "Не удалось отправить запрос.";
  const antiBotErrorText = "Подтвердите, что вы не робот.";
  const successWorkingText =
    form.dataset.msgSuccessWorkingHours ||
    "Ваш запрос отправлен. Специалист свяжется с Вами в ближайшее время.";
  const successOffHoursText =
    form.dataset.msgSuccessOffHours ||
    "Ваш запрос отправлен. Специалист свяжется с Вами в рабочее время.";

  const clearStatus = function () {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = "";
    statusEl.classList.remove(
      "feedback-form__status--success",
      "feedback-form__status--error",
      "feedback-form__status--visible"
    );
  };

  const showStatus = function (text, kind) {
    if (!statusEl) {
      return;
    }
    if (turnstileMountEl) {
      turnstileMountEl.classList.remove("feedback-form__turnstile--active");
    }
    statusEl.textContent = text;
    statusEl.classList.remove("feedback-form__status--success", "feedback-form__status--error");
    statusEl.classList.add(
      kind === "success" ? "feedback-form__status--success" : "feedback-form__status--error",
      "feedback-form__status--visible"
    );
  };

  const showTurnstileBadge = function () {
    if (!turnstileMountEl) {
      return;
    }
    clearStatus();
    turnstileMountEl.classList.add("feedback-form__turnstile--active");
  };

  const setSubmitting = function (isSubmitting) {
    if (!submitButton) {
      return;
    }
    submitButton.disabled = isSubmitting;
    submitButton.textContent = isSubmitting ? sendingText : defaultSubmitText;
  };

  const setConsentAttention = function (isActive) {
    if (!consentFieldEl) {
      return;
    }
    consentFieldEl.classList.toggle("consent--attention", Boolean(isActive));
  };

  const setInputAttention = function (isActive) {
    if (!contactInputEl) {
      return;
    }
    contactInputEl.classList.toggle("feedback-form__input--attention", Boolean(isActive));
  };

  const selectedChannels = function () {
    return Array.from(form.querySelectorAll('input[name="channel"]:checked')).map(function (el) {
      return el.value;
    });
  };

  const channelCheckboxes = Array.from(form.querySelectorAll('input[name="channel"]'));

  const ensureSingleChannel = function (changedCheckbox) {
    if (!changedCheckbox) {
      return;
    }

    if (changedCheckbox.checked) {
      channelCheckboxes.forEach(function (checkbox) {
        if (checkbox !== changedCheckbox) {
          checkbox.checked = false;
        }
      });
      return;
    }

    // Не оставляем форму без выбранного канала: возвращаем текущий чекбокс.
    if (selectedChannels().length === 0) {
      changedCheckbox.checked = true;
    }
  };

  const isMessageMode = function (channels) {
    if (channels.includes("call")) {
      return false;
    }
    return ["email", "telegram", "whatsapp", "viber"].some(function (channel) {
      return channels.includes(channel);
    });
  };

  const applyModeTexts = function () {
    const channels = selectedChannels();
    const messageMode = isMessageMode(channels);
    const emailMode = channels.includes("email");
    if (formTitleEl) {
      formTitleEl.textContent = messageMode ? messageFormTitle : callFormTitle;
    }
    if (submitButton && !submitButton.disabled) {
      submitButton.textContent = messageMode ? messageSubmitText : callSubmitText;
    }
    if (contactInputLabelEl) {
      contactInputLabelEl.textContent = emailMode ? emailInputLabel : phoneInputLabel;
    }
    if (contactInputEl) {
      contactInputEl.placeholder = emailMode ? emailInputPlaceholder : phoneInputPlaceholder;
    }
  };

  const parseErrorMessage = async function (response) {
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string" && payload.detail.trim()) {
        return payload.detail;
      }
      if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
        const firstError = payload.detail[0];
        if (typeof firstError?.msg === "string" && firstError.msg.trim()) {
          return firstError.msg;
        }
      }
    } catch (_error) {
      // Если сервер вернул не JSON, покажем fallback ниже.
    }
    return response.status === 422 ? validationErrorText : requestErrorText;
  };

  const isWorkingHours = function () {
    return Boolean(window.__WORK_HOURS_REFRESH__?.is_within_working_hours);
  };

  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const wait = function (ms) {
    return new Promise(function (resolve) {
      window.setTimeout(resolve, ms);
    });
  };
  let turnstileWidgetId = null;

  const requestTurnstileToken = async function () {
    if (!turnstileSiteKey) {
      return "";
    }
    if (!window.turnstile || !turnstileMountEl) {
      throw new Error("Turnstile не загружен");
    }

    showTurnstileBadge();

    return await new Promise(function (resolve, reject) {
      let finished = false;
      const finishOnce = function (fn, value) {
        if (finished) {
          return;
        }
        finished = true;
        fn(value);
      };

      const timerId = window.setTimeout(function () {
        finishOnce(reject, new Error("Таймаут проверки anti-bot"));
      }, 30000);

      const onSuccess = function (token) {
        window.clearTimeout(timerId);
        finishOnce(resolve, token);
      };
      const onError = function () {
        window.clearTimeout(timerId);
        finishOnce(reject, new Error("Ошибка Turnstile"));
      };
      const onExpired = function () {
        window.clearTimeout(timerId);
        finishOnce(reject, new Error("Срок проверки истек"));
      };

      if (turnstileWidgetId === null) {
        turnstileWidgetId = window.turnstile.render(turnstileMountEl, {
          sitekey: turnstileSiteKey,
          execution: "execute",
          callback: onSuccess,
          "error-callback": onError,
          "expired-callback": onExpired,
        });
      } else {
        window.turnstile.reset(turnstileWidgetId);
      }

      if (typeof window.turnstile.execute === "function") {
        window.turnstile.execute(turnstileWidgetId);
      }
    });
  };

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearStatus();

    const contactValue = String(form.elements.phone?.value || "").trim();
    const fullname = String(form.elements.fullname?.value || "").trim();
    const consent = Boolean(form.elements.consent?.checked);
    const channels = selectedChannels();
    const emailMode = channels.includes("email");
    const email = emailMode ? contactValue : null;
    const isContactValid = emailMode ? EMAIL_RE.test(contactValue) : Boolean(contactValue);
    let turnstileToken = "";

    if (!isContactValid || !consent || channels.length === 0) {
      setInputAttention(!isContactValid);
      setConsentAttention(!consent);
      showStatus(validationErrorText, "error");
      return;
    }
    setInputAttention(false);
    setConsentAttention(false);

    setSubmitting(true);
    try {
      if (turnstileSiteKey) {
        turnstileToken = await requestTurnstileToken();
        if (!turnstileToken) {
          showStatus(antiBotErrorText, "error");
          return;
        }
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: contactValue,
          email: email || null,
          fullname: fullname || null,
          turnstile_token: turnstileToken || null,
          channels: channels,
          consent: consent,
          page: page,
          lang: lang,
        }),
      });

      if (!response.ok) {
        const errorText = await parseErrorMessage(response);
        if (turnstileSiteKey) {
          await wait(1000);
        }
        showStatus(errorText, "error");
        return;
      }

      if (turnstileSiteKey) {
        await wait(1000);
      }
      showStatus(isWorkingHours() ? successWorkingText : successOffHoursText, "success");
      form.reset();
      const callCheckbox = form.querySelector('input[name="channel"][value="call"]');
      if (callCheckbox) {
        callCheckbox.checked = true;
      }
      applyModeTexts();
    } catch (_error) {
      showStatus(requestErrorText, "error");
    } finally {
      setSubmitting(false);
      applyModeTexts();
    }
  });

  channelCheckboxes.forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      ensureSingleChannel(checkbox);
      applyModeTexts();
    });
  });

  if (selectedChannels().length === 0) {
    const callCheckbox = form.querySelector('input[name="channel"][value="call"]');
    if (callCheckbox) {
      callCheckbox.checked = true;
    }
  }

  if (consentCheckboxEl) {
    consentCheckboxEl.addEventListener("change", function () {
      if (consentCheckboxEl.checked) {
        setConsentAttention(false);
      }
    });
  }

  if (contactInputEl) {
    contactInputEl.addEventListener("input", function () {
      if (String(contactInputEl.value || "").trim()) {
        setInputAttention(false);
      }
    });
  }

  applyModeTexts();
})();
