const { recipes: inspiration } = require("../../data/recipes");
const { listRecipes } = require("../../api/recipes");
const { normalizeRecipe } = require("../../utils/recipe-filter");

const PAGE_SIZE = 20;

function decorate(item) {
  return {
    ...item,
    sourceLabel: item.source_type === "ai" ? "AI 推荐" : "平台食谱",
    nutritionLabel: item.nutrition_source === "tka" ? "TKA 营养数据" : (item.nutrition_source ? "含 AI 估算" : ""),
  };
}

const defaults = inspiration.map((item, index) => decorate(normalizeRecipe(item, index, inspiration)));

function requestOptions(active, query, offset) {
  const options = { limit: PAGE_SIZE, offset };
  if (query.trim()) options.query = query.trim();
  if (active === "favorites") options.scope = "favorites";
  if (active === "quick") options.max_minutes = 15;
  if (active === "protein") options.high_protein = true;
  if (active === "vegetarian") options.tag = "vegetarian";
  return options;
}

Page({
  data: {
    active: "all", query: "", searching: false, loading: false, hasMore: true, offset: 0,
    visible: defaults,
    filters: [
      { key: "all", label: "全部" }, { key: "quick", label: "15分钟快手" },
      { key: "protein", label: "高蛋白" }, { key: "vegetarian", label: "轻素食" },
      { key: "favorites", label: "我的收藏" },
    ],
  },
  onShow() { this.load(true); },
  onReachBottom() { if (this.data.hasMore) this.load(false); },
  async load(reset) {
    this.loadRevision = (this.loadRevision || 0) + 1;
    const revision = this.loadRevision;
    if (this.data.loading) {
      this.pendingReload = this.pendingReload === true || Boolean(reset);
      return;
    }
    const offset = reset ? 0 : this.data.offset;
    const active = this.data.active;
    const query = this.data.query;
    this.setData({ loading: true });
    try {
      const remote = await listRecipes(requestOptions(active, query, offset));
      if (revision !== this.loadRevision) return;
      const next = remote.map((item, index) => decorate(normalizeRecipe(item, offset + index, inspiration)));
      this.setData({
        visible: reset ? next : [...this.data.visible, ...next],
        offset: offset + next.length,
        hasMore: next.length === PAGE_SIZE,
      });
    } catch (error) {
      console.warn("recipes", error);
      if (revision === this.loadRevision) {
        this.setData({
          visible: reset && !query && active === "all" ? defaults : this.data.visible,
          hasMore: false,
        });
      }
    } finally {
      this.setData({ loading: false }, () => {
        const pending = this.pendingReload;
        this.pendingReload = null;
        if (pending !== null && pending !== undefined) this.load(pending);
      });
    }
  },
  choose(e) { this.setData({ active: e.currentTarget.dataset.key }, () => this.load(true)); },
  open(e) { wx.setStorageSync("recipes.selected", e.detail.recipe); wx.navigateTo({ url: `/pages/recipe-detail/index?id=${e.detail.recipe.id}` }); },
  toggleSearch() { const searching = !this.data.searching; this.setData({ searching, query: searching ? this.data.query : "" }, () => this.load(true)); },
  inputSearch(e) { this.setData({ query: e.detail.value }); clearTimeout(this.searchTimer); this.searchTimer = setTimeout(() => this.load(true), 250); },
  clearSearch() { this.setData({ query: "" }, () => this.load(true)); },
  openAi() { wx.navigateTo({ url: "/pages/ai-recipes/index" }); },
});
