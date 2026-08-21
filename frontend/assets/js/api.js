const API_BASE_URL = "http://localhost:8001"; // ← update to your deployed backend URL

const DEMO_MODE = false;

// ---------- token storage ----------
function saveToken(token) {
  sessionStorage.setItem("nayisaans_token", token);
}
function getToken() {
  return sessionStorage.getItem("nayisaans_token");
}
function clearToken() {
  sessionStorage.removeItem("nayisaans_token");
}

// ---------- core request helper ----------
async function apiRequest(path, method = "GET", body = null, auth = false) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });
  } catch (networkErr) {
    throw new Error("Can't reach the server. Check your connection and try again.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    // no JSON body (e.g. 204) — fine
  }

  if (!response.ok) {
    const message = (data && (data.detail || data.error || data.message)) || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

// ---------- auth ----------
// ---------- auth ----------
async function sendSignupOtp(fullName, email, password, phone) {
  return apiRequest("/signup/send-otp", "POST", { full_name: fullName, email, password, phone });
}
async function verifySignupOtp(fullName, email, password, phone, code) {
  const data = await apiRequest("/signup/verify-otp", "POST", { full_name: fullName, email, password, phone, code });
  if (data && data.token) saveToken(data.token);
  return data;
}

async function login(email, password) {
  return apiRequest("/login", "POST", { email, password });
}
async function verifyLoginOtp(userId, code) {
  const data = await apiRequest("/login/verify-otp", "POST", { user_id: userId, code });
  if (data && data.token) saveToken(data.token);
  return data;
}
async function resendLoginOtp(userId) {
  return apiRequest("/login/resend-otp", "POST", { user_id: userId });
}

async function getCurrentUser() {
  return apiRequest("/me", "GET", null, true);
}

function logout() {
  clearToken();
}

function isLoggedIn() {
  return !!getToken();
}

// ---------- onboarding ----------
async function submitOnboarding(payload) {
  // payload: { cigs_per_day, years_smoking, brand_type, first_cig_time,
  //            gap_hours, triggers, custom_trigger, quit_reason, quit_date }
  return apiRequest("/onboarding", "POST", payload, true);
}

// ---------- checkin ----------
async function submitCheckinRequest({ type, stress, moods, note }) {
  return apiRequest("/checkin", "POST", { type, stress: Number(stress), moods, note }, true);
}

async function getCheckinsToday() {
  return apiRequest("/checkins/today", "GET", null, true);
}

// ---------- physiology ----------
async function submitPhysiology({ bpm, quality }) {
  return apiRequest("/physiology", "POST", { bpm, quality }, true);
}

// ---------- dashboard / twin ----------
async function getDashboard() {
  return apiRequest("/dashboard", "GET", null, true);
}

async function getTwinState() {
  return apiRequest("/twin/state", "GET", null, true);
}

// ---------- timeline ----------
async function getTimeline() {
  return apiRequest("/timeline", "GET", null, true);
}

// ---------- account ----------
async function deleteAccount() {
  const result = await apiRequest("/account", "DELETE", null, true);
  clearToken();
  return result;
}

// ---------- recovery tasks ----------
async function getTasks() {
  return apiRequest("/tasks", "GET", null, true);
}
async function completeTask(taskId, cravingBefore, cravingAfter) {
  return apiRequest(`/tasks/${taskId}/complete`, "POST", {
    craving_before: cravingBefore, craving_after: cravingAfter,
  }, true);
}
async function getTaskHistory() {
  return apiRequest("/tasks/history", "GET", null, true);
}

// ---------- wellness lab ----------
async function getWellnessExperiments() {
  return apiRequest("/wellness/experiments", "GET", null, true);
}

// ---------- cravings ----------
async function logCraving(payload) {
  return apiRequest("/cravings", "POST", payload, true);
}
async function getCravings() {
  return apiRequest("/cravings", "GET", null, true);
}

// ---------- journal ----------
async function addJournalEntry(payload) {
  return apiRequest("/journal", "POST", payload, true);
}
async function getJournalEntries() {
  return apiRequest("/journal", "GET", null, true);
}

// ---------- triggers ----------
async function getTriggers() {
  return apiRequest("/triggers", "GET", null, true);
}
async function addTrigger(payload) {
  return apiRequest("/triggers", "POST", payload, true);
}
async function deleteTrigger(id) {
  return apiRequest(`/triggers/${id}`, "DELETE", null, true);
}

// ---------- recovery coach ----------
async function sendCoachMessage(message) {
  return apiRequest("/coach/message", "POST", { message }, true);
}
async function getCoachHistory() {
  return apiRequest("/coach/history", "GET", null, true);
}

// ---------- my journey ----------
async function getJourney() {
  return apiRequest("/journey", "GET", null, true);
}

// ---------- analytics ----------
async function getAnalytics() {
  return apiRequest("/analytics", "GET", null, true);
}

// ---------- resources (public, no auth) ----------
async function getResources() {
  return apiRequest("/resources", "GET", null, false);
}

// ---------- profile / settings ----------
async function getSettings() {
  return apiRequest("/settings", "GET", null, true);
}
async function updateSettings(payload) {
  return apiRequest("/settings", "PUT", payload, true);
}
