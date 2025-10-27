async function doLogin(username, password) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    credentials: "include",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({username, password})
  });
  const data = await res.json();
  if (data.ok) {
    CSRF_TOKEN = data.csrf_token;
  }
  return {status: res.status, data};
}

async function doLogout() {
  const res = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: {"X-CSRF-Token": CSRF_TOKEN}
  });
  const data = await res.json();
  if (data.ok) {
    window.location.href = "index.html";
  }
}

function wireLogoutBtn() {
  const btn = document.getElementById("logoutBtn");
  if (btn) {
    btn.addEventListener("click", async () => {
      await doLogout();
    });
  }
}
