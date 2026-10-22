(function () {
  "use strict";

  var script = document.currentScript;
  var widgetId = script && script.getAttribute("data-widget-id");
  if (!widgetId) {
    console.error("[widget] missing data-widget-id attribute");
    return;
  }
  var apiBase = new URL(script.src).origin;

  var container = document.createElement("div");
  script.parentNode.insertBefore(container, script.nextSibling);

  function newKey() {
    if (window.crypto && crypto.randomUUID) { return crypto.randomUUID(); }
    return String(Date.now()) + "-" + Math.random().toString(36).slice(2);
  }

  // textContent, never innerHTML: tenant-provided text is untrusted on a third-party page.
  function element(tag, text, styles) {
    var node = document.createElement(tag);
    if (text) { node.textContent = text; }
    if (styles) { Object.assign(node.style, styles); }
    return node;
  }

  function describeErrors(body) {
    var detail = body && body.detail;
    if (Array.isArray(detail)) {
      return detail.map(function (item) {
        return (item.field ? item.field + ": " : "") + (item.msg || "invalid value");
      }).join("; ");
    }
    return typeof detail === "string" ? detail : "Please check your input.";
  }

  function render(config) {
    var form = element("form", null, { fontFamily: "system-ui, sans-serif", maxWidth: "420px" });
    form.appendChild(element("h3", config.title));
    if (config.description) { form.appendChild(element("p", config.description)); }

    var inputs = {};
    config.fields.forEach(function (field) {
      var label = element("label", field.label, { display: "block", marginTop: "8px" });
      var input = document.createElement(field.type === "textarea" ? "textarea" : "input");
      if (field.type !== "textarea") { input.type = field.type === "email" ? "email" : "text"; }
      input.required = field.required;
      input.style.display = "block";
      input.style.width = "100%";
      label.appendChild(input);
      form.appendChild(label);
      inputs[field.name] = input;
    });

    // Honeypot: invisible to people, filled in by naive bots. No name, so autofill ignores it.
    var honeypot = document.createElement("input");
    honeypot.type = "text";
    honeypot.tabIndex = -1;
    honeypot.autocomplete = "off";
    honeypot.setAttribute("aria-hidden", "true");
    Object.assign(honeypot.style, { position: "absolute", left: "-9999px" });
    form.appendChild(honeypot);

    var button = element("button", config.button_text, { marginTop: "12px" });
    button.type = "submit";
    var message = element("p");
    form.appendChild(button);
    form.appendChild(message);

    function say(text, isError) {
      message.textContent = text;
      message.style.color = isError ? "#b00020" : "#1b5e20";
    }

    var idempotencyKey = null;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      button.disabled = true;
      say("Sending...", false);

      var data = {};
      Object.keys(inputs).forEach(function (name) { data[name] = inputs[name].value; });
      // Reused on retry after a failure, so a double click cannot store two rows.
      if (!idempotencyKey) { idempotencyKey = newKey(); }

      fetch(apiBase + "/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          widget_id: config.public_id,
          data: data,
          idempotency_key: idempotencyKey,
          website: honeypot.value
        })
      })
        .then(function (response) {
          return response.json().catch(function () { return {}; }).then(function (body) {
            return { status: response.status, body: body, retryAfter: response.headers.get("Retry-After") };
          });
        })
        .then(function (result) {
          if (result.status === 200 || result.status === 201) {
            form.reset();
            idempotencyKey = null;
            say("Thank you! We received your submission.", false);
          } else if (result.status === 422) {
            say(describeErrors(result.body), true);
          } else if (result.status === 429) {
            say("Too many requests. Please try again in " + (result.retryAfter || "a few") + " seconds.", true);
          } else {
            say("Something went wrong. Please try again.", true);
          }
        })
        .catch(function () { say("Network error. Please try again.", true); })
        .then(function () { button.disabled = false; });
    });

    container.appendChild(form);
  }

  fetch(apiBase + "/public/widgets/" + encodeURIComponent(widgetId) + "/config")
    .then(function (response) {
      if (!response.ok) { throw new Error("config request failed with " + response.status); }
      return response.json();
    })
    .then(render)
    .catch(function (error) { console.error("[widget]", error); });
})();