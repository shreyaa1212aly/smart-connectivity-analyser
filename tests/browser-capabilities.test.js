const test = require("node:test");
const assert = require("node:assert/strict");
const { checkStorageCapability, detectLocation } = require("../js/script.js");

test("storage diagnostics verify a usable write and remove the temporary probe", () => {
  const values = new Map();
  const storage = {
    setItem(key, value) { values.set(key, value); },
    removeItem(key) { values.delete(key); }
  };

  assert.deepEqual(checkStorageCapability(storage), {
    supported: true,
    message: "Saved-location storage is available in this browser."
  });
  assert.equal(values.size, 0);
});

test("storage diagnostics distinguish blocked writes from available storage methods", () => {
  const storage = {
    setItem() { throw new Error("Storage is blocked"); },
    removeItem() {}
  };

  assert.equal(checkStorageCapability(storage).supported, false);
  assert.match(checkStorageCapability(storage).message, /blocked or full/);
});

test("real geolocation error callback explains denied permission", () => {
  const previousDocument = global.document;
  const elements = new Map();
  global.document = {
    getElementById(id) {
      if (id === "toast") return { classList: { add() {}, remove() {} } };
      if (id === "toast-message") return { textContent: "" };
      if (!elements.has(id)) elements.set(id, { textContent: "" });
      return elements.get(id);
    }
  };

  try {
    const geolocation = {
      getCurrentPosition(_success, onError) {
        onError({ code: 1 });
      }
    };

    detectLocation(geolocation);
    assert.match(elements.get("locationResult").textContent, /permission denied/i);
    assert.match(elements.get("geolocationCapability").textContent, /browser site settings/i);
  } finally {
    if (previousDocument === undefined) delete global.document;
    else global.document = previousDocument;
  }
});

test("unsupported geolocation updates only its own diagnostic", () => {
  const previousDocument = global.document;
  const elements = new Map();
  global.document = {
    getElementById(id) {
      if (id === "toast") return { classList: { add() {}, remove() {} } };
      if (id === "toast-message") return { textContent: "" };
      if (!elements.has(id)) elements.set(id, { textContent: "" });
      return elements.get(id);
    }
  };

  try {
    detectLocation(null);
    assert.match(elements.get("locationResult").textContent, /not supported/i);
    assert.match(elements.get("geolocationCapability").textContent, /unavailable/i);
    assert.equal(elements.has("storageCapability"), false);
  } finally {
    if (previousDocument === undefined) delete global.document;
    else global.document = previousDocument;
  }
});
