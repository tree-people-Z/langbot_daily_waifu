# 每日签到与抽老婆（LangBot）

LangBot 4.x 插件，包含每日签到、积分、排行榜、今日老婆和积分换老婆。图片来源支持本地图库或漫朔。

## 命令

命令前缀由 LangBot 配置（常见为 `!`），以下示例假设前缀为 `!`：

- `!签到`：签到
- `!我的信息`：查询积分、连签、总签到和今日老婆
- `!排行榜`：查看积分榜
- `!老婆`：抽取今日老婆
- `!换老婆`：消耗积分重新抽取

LangBot 命令组件根据宿主配置的命令前缀触发；可在 LangBot 设置中选择命令前缀。

## 图源

- `local`：`local_wife_paths` 填 JSON 数组，可填写图片文件或目录。目录递归扫描 jpg/jpeg/png/gif/webp/bmp；可用文件名作为角色名。
- `manshuo`：直接从 `https://web.manshuo.ink/api/img/today_wife` 获取图片，缓存到插件数据目录后发送，无需配置地址或 API Key。

本地图片路径必须能被 Plugin Runtime 访问。容器部署时，需要把图库挂载到 Runtime 容器，并填写容器内绝对路径。

## 数据

SQLite 数据库和漫朔图片缓存保存在插件目录下的 `data/`。升级或重建 Runtime 时，请保留该目录。插件 DB 使用与 AstrBot 版本相同的 `users` / `daily_wife` 表结构，可将原数据库中这两张表导入以保留积分和今日老婆记录；插件不会自动迁移 AstrBot 数据库。

默认连签奖励为每连续签到一天加 50 积分，上限 500 积分，与膨胀后的运势积分档位匹配。调整基础积分时可直接修改“签到积分倍率”，无需编辑 JSON；高级用户仍可通过“运势等级 JSON”完全自定义档位。签到回复使用 Markdown 格式文本。其他配置包括时区、榜单范围、图源、本地图片路径、换老婆成本和次数上限。

## 调试

安装 `requirements.txt` 后，在插件目录运行 `lbp run` 连接 LangBot Plugin Runtime 调试；运行 `lbp build` 打包。

本插件移植自 GPL-3.0 授权的 AstrBot 插件，并按 GPL-3.0 发布，见 `LICENSE`。
