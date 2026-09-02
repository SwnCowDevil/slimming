const { calendarStyle } = require("./theme");
Component({
  properties: { marks: { type: Array, value: [] } },
  data: { calendarStyle, areas: ["header", "title", "today", "viewbar", "dragbar"] },
  methods: {
    change(event) { this.triggerEvent("datechange", event.detail); },
    viewChange(event) { this.triggerEvent("viewchange", event.detail); },
  },
});
