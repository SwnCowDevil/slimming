# TKA 食品数据运维

本项目使用爱沙尼亚 TKA/TAP 免费食品成分数据的可追溯导入适配层。运行服务时不抓取网页；先按许可获得并整理官方导出文件，再离线导入。

每条食品记录保存：数据提供方、数据集版本、来源食品 ID、来源 URL、FoodEx2 分类、原始行 SHA-256 和营养计算方法。餐食记录保存当时的营养快照，因此后续更新目录不会改写历史。

## 导入

```sh
export SLIMMING_ADMIN_IMPORT_KEY='与 backend/.env 一致的独立管理密钥'
./scripts/import-tka-dataset.sh /absolute/path/to/tka.json 2026-08 --dry-run
./scripts/import-tka-dataset.sh /absolute/path/to/tka.json 2026-08 --execute
```

脚本会先将源文件复制到后端允许的 `data/imports` 目录；dry-run 使用临时副本并在完成后删除，正式导入则保留带版本号的归档副本。

导入前应检查：

- 文件来自 `tka.nutridata.ee` 或 `tap.nutridata.ee` 的合法公开导出；
- 数据集版本非空并可追溯；
- 能量单位与每 100 克基准明确；
- 中文名称是本地别名，不覆盖原始英文/爱沙尼亚文名称；
- 执行前先看 dry-run 报告，保留导入日志和原始文件。

重复导入同一来源、食品 ID 和版本是幂等的。数据回滚应发布新版本并停用错误记录，不直接修改已生成的历史餐食快照。
