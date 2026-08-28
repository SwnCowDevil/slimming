# 孕食记

面向孕期的原生微信小程序。产品围绕每日餐单、饮食与体重记录、已审核食谱、孕期趋势、家庭协作和受限 AI 辅助展开；后端使用 FastAPI，食品成分通过爱沙尼亚 TKA 数据的可追溯离线导入适配层提供。

本仓库中的 `prototype/` 与 `superdesign/` 仅是设计参考，不能作为线上前端构建或运行入口。实际客户端始终位于 `miniprogram/`，使用 WXML、WXSS 和 JavaScript。

## 当前产品边界

- 仅覆盖孕期；暂不提供备孕和产后模式。
- 不展示孕期目标体重、热量赤字、掉秤或断食建议。
- 食谱 Tab 保留原生小程序原有信息结构和视觉风格，叠加已审核孕期元数据。
- 家属使用独立微信身份，所有读取与代记由服务端逐项校验，孕妇可撤销授权。
- AI 只开放食物候选、食谱替换解释和周记录整理等白名单流程，不能代替专业医疗意见。

## 快速开始

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -e 'backend[dev]'
cp backend/.env.example backend/.env
npm install --prefix miniprogram
./scripts/start-local.sh
./scripts/open-wechat-devtools.sh
```

本地后端默认监听 `http://127.0.0.1:8000`。若端口被占用，可使用 `LOCAL_PORT=18080 ./scripts/start-local.sh`，并同步修改 `miniprogram/config/env.js` 的开发环境地址。

真实微信 AppSecret、JWT 密钥、AI 密钥、上传私钥和服务器配置不得提交到仓库。

## 文档

- [孕期版产品与数据架构](docs/superpowers/specs/2026-08-27-pregnancy-product-data-architecture-design.md)
- [实施计划](docs/superpowers/plans/2026-08-28-pregnancy-product-implementation.md)
- [API 与微信身份](docs/api.md)
- [本地启动、后端部署和小程序上传](docs/deployment.md)
- [TKA 数据导入运维](docs/tka-data-operations.md)
- [小程序验收清单](miniprogram/qa/acceptance-checklist.md)
