const SESSION_KEY = "slimming.session.v1";
let memorySession = null;

function shouldReuseSession(session, now = Date.now()) {
  return Boolean(session && session.token && session.userId && session.expiresAt > now + 30_000);
}

function readSession() {
  if (memorySession) return memorySession;
  if (typeof wx !== "undefined") memorySession = wx.getStorageSync(SESSION_KEY) || null;
  return memorySession;
}

function saveSession(session) {
  memorySession = session;
  if (typeof wx !== "undefined") wx.setStorageSync(SESSION_KEY, session);
  return session;
}

function clearSession() {
  memorySession = null;
  if (typeof wx !== "undefined") wx.removeStorageSync(SESSION_KEY);
}

module.exports = { SESSION_KEY, shouldReuseSession, readSession, saveSession, clearSession };
