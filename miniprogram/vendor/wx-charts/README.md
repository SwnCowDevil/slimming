# Vendored wx-charts

- Upstream: `https://github.com/xiaolin3303/wx-charts`
- Commit: `13fdd6475d8ce782161a181c76f0e61706b25b4b`
- Vendored file: `dist/wxcharts.js`
- License: MIT, preserved in `LICENSE`

The application imports this pinned local copy so chart behavior is auditable and does not depend on a runtime CDN.

Project patch: the constructor passes an optional `component` instance as the second argument to `wx.createCanvasContext`, allowing the library to render inside the reusable `health-chart` custom component.
