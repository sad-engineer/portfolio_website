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
  const statusEl = document.getElementById("feedback-form-status");
  const endpoint = form.dataset.feedbackEndpoint || "/api/feedback";
  const lang = form.dataset.feedbackLang || "ru";
  const page = form.dataset.feedbackPage || window.location.pathname;

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
    statusEl.classList.remove("feedback-form__status--success", "feedback-form__status--error");
  };

  const showStatus = function (text, kind) {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = text;
    statusEl.classList.remove("feedback-form__status--success", "feedback-form__status--error");
    statusEl.classList.add(kind === "success" ? "feedback-form__status--success" : "feedback-form__status--error");
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

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearStatus();

    const contactValue = String(form.elements.phone?.value || "").trim();
    const consent = Boolean(form.elements.consent?.checked);
    const channels = selectedChannels();
    const emailMode = channels.includes("email");
    const email = emailMode ? contactValue : null;
    const isContactValid = emailMode ? EMAIL_RE.test(contactValue) : Boolean(contactValue);

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
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: contactValue,
          email: email || null,
          channels: channels,
          consent: consent,
          page: page,
          lang: lang,
        }),
      });

      if (!response.ok) {
        const errorText = await parseErrorMessage(response);
        showStatus(errorText, "error");
        return;
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
