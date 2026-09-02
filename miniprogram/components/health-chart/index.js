const WxCharts = require("../../vendor/wx-charts/wxcharts");
const {
  buildWeightOptions,
  buildCalorieOptions,
  buildPregnancyWeightOptions,
  buildPregnancyCalorieOptions,
} = require("./options");

let sequence = 0;

Component({
  properties: {
    title: String,
    type: { type: String, value: "weight" },
    points: { type: Array, value: [] },
    height: { type: Number, value: 190 },
  },
  data: { canvasId: "", width: 320, empty: true },
  lifetimes: {
    attached() {
      sequence += 1;
      this.setData({ canvasId: `health-chart-${sequence}` });
    },
    ready() {
      this.measureAndDraw();
    },
    detached() {
      if (this.chart) this.chart.stopAnimation();
    },
  },
  observers: {
    points() {
      if (this.data.canvasId) this.measureAndDraw();
    },
  },
  methods: {
    measureAndDraw() {
      this.createSelectorQuery().select(".chart-shell").boundingClientRect((rect) => {
        if (!rect) return;
        const width = Math.max(260, Math.floor(rect.width - 24));
        const builders = {
          calorie: buildCalorieOptions,
          "pregnancy-weight": buildPregnancyWeightOptions,
          "pregnancy-calorie": buildPregnancyCalorieOptions,
        };
        const builder = builders[this.data.type] || buildWeightOptions;
        const options = builder(this.data.points, width, this.data.height);
        this.setData({ width, empty: !options }, () => {
          if (!options) return;
          this.chart = new WxCharts({ ...options, canvasId: this.data.canvasId, component: this });
          if (options.enableScroll) this.scrollToLatest();
        });
      }).exec();
    },
    scrollToLatest() {
      this.chart.scrollStart({ touches: [{ x: this.data.width }] });
      this.chart.scroll({ touches: [{ x: -100000 }] });
      this.chart.scrollEnd({});
    },
    touchStart(event) {
      if (this.chart) this.chart.scrollStart(event);
    },
    touchMove(event) {
      if (this.chart) this.chart.scroll(event);
    },
    touchEnd(event) {
      if (!this.chart) return;
      this.chart.scrollEnd(event);
      this.chart.showToolTip(event, { format: (item) => `${item.name}: ${item.data}` });
    },
  },
});
