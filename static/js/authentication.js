(function() {
  const DEBOUNCE_MS = 450;

  // Inputs
  const usernameInput = document.getElementById('id_username');
  const emailInput = document.getElementById('id_email');
  const phoneInput = document.getElementById('id_phone_number');

  // Feedback elements
  const usernameFeedback = document.getElementById('username-feedback');
  const emailFeedback = document.getElementById('email-feedback');
  const phoneFeedback = document.getElementById('phone-feedback');

  // Spinners
  const usernameSpinner = document.getElementById('username-spinner');
  const emailSpinner = document.getElementById('email-spinner');
  const phoneSpinner = document.getElementById('phone-spinner');

  function setFeedback(el, message, type) {
    if (!el) return;
    el.textContent = message || '';
    el.classList.remove('text-red-500', 'text-green-600', 'text-gray-500');
    if (type === 'error') el.classList.add('text-red-500');
    else if (type === 'available') el.classList.add('text-green-600');
    else el.classList.add('text-gray-500');
  }

  function setInputState(input, state) {
    if (!input) return;
    input.classList.remove('border-red-500', 'border-green-500', 'border-yellow-500', 'focus:ring-red-200', 'focus:ring-green-200', 'focus:ring-yellow-200');
    if (state === 'available') {
      input.classList.add('border-green-500', 'focus:ring-green-200');
    } else if (state === 'unavailable') {
      // warning (orange/yellowish)
      input.classList.add('border-yellow-500', 'focus:ring-yellow-200');
    } else if (state === 'error') {
      input.classList.add('border-red-500', 'focus:ring-red-200');
    }
  }

  function defaultValidateEmail(value) {
    const v = value.trim();
    if (v.length === 0) return { valid: false, message: '' };
    // simple email regexp
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(v)) return { valid: false, message: 'Enter a valid email address.' };
    return { valid: true };
  }

  function defaultValidatePhone(value) {
    const v = value.trim();
    if (v.length === 0) return { valid: false, message: '' };
    const digits = v.replace(/\D/g, '');
    if (digits.length < 10 || digits.length > 15) return { valid: false, message: 'Phone must be 10–15 digits.' };
    return { valid: true, cleaned: digits };
  }

  function setupCheck(options) {
    const { input, spinner, feedback, url, paramName, validate } = options;
    if (!input || !feedback) return;

    let timeout = null;

    input.addEventListener('input', function() {
      const value = this.value;
      setFeedback(feedback, '', null);
      if (timeout) clearTimeout(timeout);

      if (!value || value.trim().length === 0) {
        if (spinner) spinner.classList.add('hidden');
        setFeedback(feedback, '', null);
        input.removeAttribute('aria-busy');
        return;
      }

      timeout = setTimeout(() => {
        const v = value.trim();
        const result = validate ? validate(v) : { valid: true };
        if (!result.valid) {
          setFeedback(feedback, result.message || '', 'error');
          if (spinner) spinner.classList.add('hidden');
          input.removeAttribute('aria-busy');
          return;
        }

        // show spinner / mark busy
        if (spinner) spinner.classList.remove('hidden');
        input.setAttribute('aria-busy', 'true');

        const paramValue = result.cleaned ? result.cleaned : v;
        const q = `${paramName}=${encodeURIComponent(paramValue)}`;

        fetch(`${url}?${q}`)
          .then(r => r.json())
            .then(data => {
              if (data && data.exists) {
                // exists -> unavailable (warning)
                setFeedback(feedback, data.message || 'Already in use.', 'unavailable');
                setInputState(input, 'unavailable');
              } else {
                setFeedback(feedback, (data && data.message) || 'Available.', 'available');
                setInputState(input, 'available');
              }
          })
          .catch(err => {
            console.error('Availability check error:', err);
            setFeedback(feedback, 'Could not check availability.', '');
            setInputState(input, 'error');
          })
          .finally(() => {
            if (spinner) spinner.classList.add('hidden');
            input.removeAttribute('aria-busy');
          });
      }, DEBOUNCE_MS);
    });
  }

  // Setup username check
  setupCheck({
    input: usernameInput,
    spinner: usernameSpinner,
    feedback: usernameFeedback,
    url: '/auth/ajax/check-username/',
    paramName: 'username',
    validate: (v) => ({ valid: v.trim().length > 0 })
  });

  // Setup email check
  setupCheck({
    input: emailInput,
    spinner: emailSpinner,
    feedback: emailFeedback,
    url: '/auth/ajax/check-email/',
    paramName: 'email',
    validate: defaultValidateEmail
  });

  // Setup phone check
  setupCheck({
    input: phoneInput,
    spinner: phoneSpinner,
    feedback: phoneFeedback,
    url: '/auth/ajax/check-phone/',
    paramName: 'phone',
    validate: defaultValidatePhone
  });

  // Password field outlining on simple client-side validation
  const pw1 = document.getElementById('id_password1');
  const pw2 = document.getElementById('id_password2');

  function validatePasswords() {
    if (!pw1) return;
    const v1 = pw1.value || '';
    const v2 = pw2 ? pw2.value || '' : '';
    // Basic rules: at least 8 chars
    if (v1.length > 0 && v1.length < 8) {
      setInputState(pw1, 'error');
    } else {
      setInputState(pw1, null);
    }

    if (pw2) {
      if (v2.length > 0 && v2 !== v1) {
        setInputState(pw2, 'error');
      } else if (v2.length > 0 && v2 === v1 && v1.length >= 8) {
        setInputState(pw2, 'available');
      } else {
        setInputState(pw2, null);
      }
    }
  }

  if (pw1) pw1.addEventListener('input', validatePasswords);
  if (pw2) pw2.addEventListener('input', validatePasswords);

  // On page load, if server rendered field errors exist, outline inputs red
  document.addEventListener('DOMContentLoaded', function() {
    const fieldsToCheck = [
      {input: usernameInput},
      {input: emailInput},
      {input: phoneInput},
      {input: pw1},
      {input: pw2}
    ];
    fieldsToCheck.forEach(({input}) => {
      if (!input) return;
      const parent = input.closest('div');
      if (!parent) return;
      const err = parent.querySelector('p.text-red-500');
      if (err) setInputState(input, 'error');
    });
  });

})();