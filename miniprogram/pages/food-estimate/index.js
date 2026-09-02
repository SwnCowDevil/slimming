const { localDateKey } = require("../../utils/date");

const CATEGORIES = [
  { key: "staple", label: "主食" },
  { key: "protein", label: "肉蛋" },
  { key: "seafood", label: "水产" },
  { key: "soy", label: "豆制品" },
  { key: "vegetable", label: "蔬菜" },
  { key: "fruit", label: "水果" },
  { key: "dairy", label: "奶类" },
  { key: "fat", label: "坚果油脂" },
];

const REFERENCES = [
  { id: "rice", category: "staple", name: "熟米饭", reference: "1 小碗", detail: "普通家用小碗盛至八分满", gramsMin: 100, gramsMax: 150, keyword: "米饭" },
  { id: "noodles", category: "staple", name: "熟面条", reference: "1 中碗", detail: "不含大量汤汁的面条", gramsMin: 180, gramsMax: 250, keyword: "面条" },
  { id: "sweet-potato", category: "staple", name: "红薯", reference: "1 拳头大小", detail: "蒸熟后约一个成人拳头", gramsMin: 150, gramsMax: 200, keyword: "红薯" },
  { id: "meat", category: "protein", name: "熟瘦肉", reference: "1 掌心", detail: "不含手指，厚度约一指", gramsMin: 70, gramsMax: 100, keyword: "瘦肉" },
  { id: "egg", category: "protein", name: "鸡蛋", reference: "1 个", detail: "普通中等大小，去壳后估算", gramsMin: 45, gramsMax: 55, keyword: "鸡蛋" },
  { id: "fish", category: "seafood", name: "熟鱼肉", reference: "1 掌心", detail: "去骨后约一个掌心大小", gramsMin: 80, gramsMax: 120, keyword: "鱼肉" },
  { id: "shrimp", category: "seafood", name: "熟虾仁", reference: "10 只中等大小", detail: "去头去壳后估算", gramsMin: 70, gramsMax: 100, keyword: "虾仁" },
  { id: "tofu", category: "soy", name: "北豆腐", reference: "1 掌心", detail: "约一个掌心大小、一指厚", gramsMin: 80, gramsMax: 120, keyword: "豆腐" },
  { id: "leafy-greens", category: "vegetable", name: "熟叶菜", reference: "双手一捧", detail: "沥去明显汤汁后估算", gramsMin: 150, gramsMax: 250, keyword: "叶菜" },
  { id: "apple", category: "fruit", name: "苹果", reference: "1 拳头大小", detail: "可食部分，不含果核", gramsMin: 150, gramsMax: 200, keyword: "苹果" },
  { id: "banana", category: "fruit", name: "香蕉", reference: "1 根中等大小", detail: "去皮后的可食部分", gramsMin: 90, gramsMax: 120, keyword: "香蕉" },
  { id: "milk", category: "dairy", name: "牛奶", reference: "1 杯", detail: "普通水杯约一杯", gramsMin: 200, gramsMax: 250, keyword: "牛奶" },
  { id: "nuts", category: "fat", name: "坚果", reference: "1 小把", detail: "能在掌心平铺一层", gramsMin: 10, gramsMax: 15, keyword: "坚果" },
  { id: "oil", category: "fat", name: "食用油", reference: "1 茶匙", detail: "家用小茶匙一平勺", gramsMin: 5, gramsMax: 5, keyword: "食用油" },
];

function normalizePortions(value) {
  return Math.min(5, Math.max(0.5, Math.round(value * 2) / 2));
}

function presentItem(item, portions = 1) {
  const amount = normalizePortions(portions);
  const min = Math.round(item.gramsMin * amount);
  const max = Math.round(item.gramsMax * amount);
  return {
    ...item,
    portions: amount,
    portionsLabel: Number.isInteger(amount) ? String(amount) : amount.toFixed(1),
    gramsLabel: min === max ? `约 ${min} 克` : `约 ${min}–${max} 克`,
  };
}

function itemsFor(category, portions = {}) {
  return REFERENCES
    .filter((item) => item.category === category)
    .map((item) => presentItem(item, portions[item.id] || 1));
}

Page({
  data: {
    mealDate: localDateKey(),
    categories: CATEGORIES,
    activeCategory: "staple",
    visibleItems: itemsFor("staple"),
    portions: {},
  },
  onLoad(query = {}) {
    this.setData({ mealDate: query.date || localDateKey() });
  },
  selectCategory(event) {
    const activeCategory = event.currentTarget.dataset.key;
    this.setData({ activeCategory, visibleItems: itemsFor(activeCategory, this.data.portions) });
  },
  adjust(event) {
    const { id, delta } = event.currentTarget.dataset;
    const current = this.data.portions[id] || 1;
    const portions = { ...this.data.portions, [id]: normalizePortions(current + Number(delta) * 0.5) };
    this.setData({ portions, visibleItems: itemsFor(this.data.activeCategory, portions) });
  },
  record(event) {
    const keyword = event.currentTarget.dataset.keyword;
    wx.navigateTo({ url: `/pages/food-search/index?date=${this.data.mealDate}&q=${encodeURIComponent(keyword)}` });
  },
});
