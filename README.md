# Daily Check-in & Waifu

A LangBot 4.x plugin for daily check-in, points, leaderboards, and daily waifu draws from a local image gallery or Manshuo.

## Commands

Commands use a prefix enabled in LangBot (`!`, `！`, or `/` in the provided container configuration). The commands are `签到`, `我的信息`, `排行榜`, `老婆`, and `换老婆`; for example: `/签到`, `/老婆`, and `/换老婆`.

The default check-in streak bonus is 50 points per consecutive day, capped at 500 points. Use the `签到积分倍率` setting to scale every fortune tier's base reward without editing JSON. The default cost to change a waifu is 3000 points.

All replies use clean plain text for reliable group delivery. Image replies are returned as Base64 message content, so container deployments do not require a separate Box Runtime or host file-transfer service.

## Image sources

- `local`: configure `local_wife_paths` as a JSON array of image files or directories. Directories are scanned recursively. Supported extensions: jpg, jpeg, png, gif, webp, bmp. File names can be used as character names.
- `manshuo`: downloads the image from `https://web.manshuo.ink/api/img/today_wife` into the plugin data directory so it can be sent as a local image. No URL or API key configuration is needed.

Local paths must be visible inside the Plugin Runtime environment. For containers, mount the gallery into the runtime container and configure its in-container absolute path.

## Data

SQLite data and cached Manshuo images are stored under `data/` in this plugin directory. Keep that directory persistent when upgrading or recreating the runtime.

## Development

Install dependencies with `pip install -r requirements.txt`. Validate and debug with `lbp run`; package with `lbp build`.

The source logic was migrated from the GPL-3.0 licensed AstrBot plugin, so this plugin is also distributed under GPL-3.0. See `LICENSE`.

