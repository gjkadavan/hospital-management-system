let CSRF_TOKEN = "";

// Helper: GET request with cookies.
async function apiGet(path) {
  const res = await fetch(path, {
    method: "GET",
    credentials: "include"
  });
  const data = await res.json().catch(() => ({}));

  // Capture/refresh CSRF token if provided
  if (data && data.csrf_token) {
    CSRF_TOKEN = data.csrf_token;
  }
  return { status: res.status, data };
}

// Helper: POST request with JSON body and CSRF
async function apiPost(path, bodyObj) {
  const res = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": CSRF_TOKEN
    },
    body: JSON.stringify(bodyObj || {})
  });
  const data = await res.json().catch(() => ({}));
  // token may rotate
  if (data && data.csrf_token) {
    CSRF_TOKEN = data.csrf_token;
  }
  return { status: res.status, data };
}

// Helper: PUT request with JSON body and CSRF
async function apiPut(path, bodyObj) {
  const res = await fetch(path, {
    method: "PUT",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": CSRF_TOKEN
    },
    body: JSON.stringify(bodyObj || {})
  });
  const data = await res.json().catch(() => ({}));
  if (data && data.csrf_token) {
    CSRF_TOKEN = data.csrf_token;
  }
  return { status: res.status, data };
}

// Ensures user is logged in before allowing page access.
// If not logged in -> redirect to login page.
async function ensureAuthOrRedirect() {
  const { status, data } = await apiGet("/api/auth/me");
  if (!data.ok) {
    window.location.href = "index.html";
    return null;
  }
  // user is logged in
  if (data.csrf_token) {
    CSRF_TOKEN = data.csrf_token;
  }
  return data.user;
}
