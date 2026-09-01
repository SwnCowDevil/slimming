import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);

function loadFamilyPage({ family = {}, pregnancy = {} } = {}) {
  const familyApi = require("../api/family.js");
  const pregnancyApi = require("../api/pregnancy.js");
  const familyOriginals = {};
  const pregnancyOriginals = {};
  for (const [key, value] of Object.entries(family)) {
    familyOriginals[key] = familyApi[key];
    familyApi[key] = value;
  }
  for (const [key, value] of Object.entries(pregnancy)) {
    pregnancyOriginals[key] = pregnancyApi[key];
    pregnancyApi[key] = value;
  }

  let definition;
  global.Page = (page) => { definition = page; };
  delete require.cache[require.resolve("../pages/family/index.js")];
  require("../pages/family/index.js");
  delete global.Page;

  Object.assign(familyApi, familyOriginals);
  Object.assign(pregnancyApi, pregnancyOriginals);
  return definition;
}

function mountPage(definition, data = {}) {
  return {
    ...definition,
    data: { ...definition.data, ...data },
    setData(update) {
      Object.assign(this.data, update);
    },
  };
}

test("family page enables invitation join for a user without an active family", async () => {
  const page = mountPage(loadFamilyPage({
    family: { listMembers: async () => ({ items: [] }) },
    pregnancy: { getCurrentPregnancy: async () => { throw new Error("no pregnancy"); } },
  }));

  await page.load();

  assert.equal(page.data.mode, "partner");
  assert.equal(page.data.canJoinFamily, true);
});

test("joining a family trims the invitation and reloads membership", async () => {
  const acceptedTokens = [];
  const toasts = [];
  const definition = loadFamilyPage({
    family: {
      acceptInvitation: async (token) => {
        acceptedTokens.push(token);
        return {
          id: "membership-1",
          pregnancy_episode_id: "episode-1",
          owner_user_id: "owner-1",
          member_user_id: "member-1",
          role: "partner",
          status: "active",
          permission_scopes: ["pregnancy:read", "meal:read"],
          joined_at: "2026-09-01T00:00:00Z",
          revoked_at: null,
        };
      },
    },
  });
  const page = mountPage(definition, {
    joinInvitationToken: "  abcdefghijklmnop  ",
    canJoinFamily: true,
  });
  let reloads = 0;
  page.load = async () => { reloads += 1; };
  global.wx = { showToast(options) { toasts.push(options); } };

  await page.joinFamily();

  assert.deepEqual(acceptedTokens, ["abcdefghijklmnop"]);
  assert.equal(page.data.joinInvitationToken, "");
  assert.equal(page.data.joining, false);
  assert.equal(reloads, 1);
  assert.equal(toasts.at(-1).title, "已加入家庭");
  delete global.wx;
});

test("joining rejects an incomplete invitation before requesting", async () => {
  let requests = 0;
  const toasts = [];
  const page = mountPage(loadFamilyPage({
    family: { acceptInvitation: async () => { requests += 1; } },
  }), { joinInvitationToken: "short" });
  global.wx = { showToast(options) { toasts.push(options); } };

  await page.joinFamily();

  assert.equal(requests, 0);
  assert.equal(toasts.at(-1).title, "请输入完整的邀请码");
  delete global.wx;
});

test("joining displays the backend invitation error", async () => {
  const toasts = [];
  const page = mountPage(loadFamilyPage({
    family: {
      acceptInvitation: async () => {
        throw { statusCode: 410, data: { detail: "邀请已过期" } };
      },
    },
  }), { joinInvitationToken: "abcdefghijklmnop", canJoinFamily: true });
  global.wx = { showToast(options) { toasts.push(options); } };

  await page.joinFamily();

  assert.equal(page.data.joining, false);
  assert.equal(toasts.at(-1).title, "邀请已过期");
  delete global.wx;
});
