/* Auth utility — shared across all UI pages */
window.Auth = (() => {
  const K = {
    token: "docuextract_token",
    name: "docuextract_name",
    email: "docuextract_email"
  };

  function getToken() { 
    const t = localStorage.getItem(K.token) || "";
    return t && t !== "undefined" && t !== "null" ? t : "";
  }
  
  function getName() { 
    const n = localStorage.getItem(K.name) || "User";
    return n && n !== "undefined" && n !== "null" ? n : "User";
  }
  
  function getEmail() { 
    const e = localStorage.getItem(K.email) || "";
    return e && e !== "undefined" && e !== "null" ? e : "";
  }
  
  function isLoggedIn() { 
    const token = getToken();
    if (!token) return false;
    
    // Basic JWT expiry check (decode payload)
    try {
      const parts = token.split(".");
      if (parts.length !== 3) return false;
      const payload = JSON.parse(atob(parts[1]));
      if (payload.exp && payload.exp < Date.now() / 1000) {
        logout();
        return false;
      }
      return true;
    } catch (e) {
      return !!token;
    }
  }

  function setSession(token, name, email) {
    if (!token || typeof token !== "string") {
      console.error("Invalid token provided to setSession");
      return;
    }
    localStorage.setItem(K.token, token);
    localStorage.setItem(K.name, name || "User");
    localStorage.setItem(K.email, email || "");
    console.log("Session set for:", email);
  }

  function logout() {
    localStorage.removeItem(K.token);
    localStorage.removeItem(K.name);
    localStorage.removeItem(K.email);
    window.location.href = "/ui/login";
  }

  function requireAuth() {
    if (!isLoggedIn()) {
      console.log("Not logged in, redirecting to /ui/login");
      window.location.href = "/ui/login";
      throw new Error("Not logged in");
    }
  }

  function authHeaders() {
    const token = getToken();
    return token ? { "Authorization": "Bearer " + token } : {};
  }

  async function fetchAuth(url, opts = {}) {
    opts.headers = { ...(opts.headers || {}), ...authHeaders() };
    const res = await fetch(url, opts);
    if (res.status === 401) { 
      console.log("401 Unauthorized, logging out");
      logout(); 
      return res; 
    }
    return res;
  }

  return { getToken, getName, getEmail, isLoggedIn, setSession, logout, requireAuth, authHeaders, fetchAuth };
})();