const KEY = "slimming.offline-drafts.v1";

function reconcileDrafts(local, remote) {
  const byId = new Map();
  [...remote, ...local].forEach((draft) => {
    const current = byId.get(draft.id);
    if (!current || draft.updatedAt > current.updatedAt) byId.set(draft.id, draft);
  });
  return [...byId.values()].sort((a, b) => b.updatedAt - a.updatedAt);
}

function readOfflineDrafts() { return typeof wx === "undefined" ? [] : wx.getStorageSync(KEY) || []; }
function saveOfflineDraft(draft) {
  const next = reconcileDrafts([{ ...draft, updatedAt: Date.now(), status: "local-draft" }], readOfflineDrafts());
  if (typeof wx !== "undefined") wx.setStorageSync(KEY, next);
  return next;
}
function clearOfflineDraft(id) {
  const next = readOfflineDrafts().filter((draft) => draft.id !== id);
  if (typeof wx !== "undefined") wx.setStorageSync(KEY, next);
}

module.exports = { KEY, reconcileDrafts, readOfflineDrafts, saveOfflineDraft, clearOfflineDraft };
