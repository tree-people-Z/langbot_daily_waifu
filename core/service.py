"""Check-in, points, leaderboard and daily waifu business logic."""

from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import aiosqlite
import httpx

DEFAULT_TIERS = [
    {"name": "大凶", "weight": 3, "min_points": 10, "max_points": 50},
    {"name": "凶", "weight": 7, "min_points": 60, "max_points": 150},
    {"name": "小凶", "weight": 10, "min_points": 160, "max_points": 250},
    {"name": "末吉", "weight": 15, "min_points": 260, "max_points": 400},
    {"name": "小吉", "weight": 20, "min_points": 410, "max_points": 550},
    {"name": "中吉", "weight": 20, "min_points": 560, "max_points": 700},
    {"name": "吉", "weight": 15, "min_points": 710, "max_points": 850},
    {"name": "大吉", "weight": 8, "min_points": 860, "max_points": 990},
    {"name": "超大吉", "weight": 2, "min_points": 10000, "max_points": 10000},
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class DailyService:
    def __init__(self, config: dict):
        self.config = config
        self.root = Path(__file__).resolve().parents[1]
        self.data_dir = self.root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "daily_checkin_waifu.db"
        self._db_lock = asyncio.Lock()
        self._initialized = False

    def _int(self, key: str, default: int) -> int:
        try:
            return int(self.config.get(key, default))
        except (TypeError, ValueError):
            return default

    def _timezone(self) -> timezone:
        return timezone(timedelta(hours=max(-12, min(14, self._int("timezone", 8)))))

    def today(self) -> str:
        return datetime.now(self._timezone()).date().isoformat()

    def tiers(self) -> list[dict]:
        raw = self.config.get("fortune_tiers", "")
        if isinstance(raw, str) and raw.strip():
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = []
        valid = []
        if isinstance(raw, list):
            for row in raw:
                if not isinstance(row, dict):
                    continue
                try:
                    low, high = int(row.get("min_points", 10)), int(row.get("max_points", 100))
                    valid.append({
                        "name": str(row.get("name") or "小吉"),
                        "weight": max(0, int(row.get("weight", 10))),
                        "min_points": min(low, high),
                        "max_points": max(low, high),
                    })
                except (TypeError, ValueError):
                    continue
        return valid or [dict(row) for row in DEFAULT_TIERS]

    async def _ensure_db(self):
        if self._initialized:
            return
        async with self._db_lock:
            if self._initialized:
                return
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                      sender_id TEXT NOT NULL, scope_id TEXT NOT NULL DEFAULT '',
                      points INTEGER NOT NULL DEFAULT 0, streak INTEGER NOT NULL DEFAULT 0,
                      last_checkin_date TEXT, total_checkins INTEGER NOT NULL DEFAULT 0,
                      sender_name TEXT, PRIMARY KEY(sender_id, scope_id));
                    CREATE TABLE IF NOT EXISTS daily_wife (
                      sender_id TEXT NOT NULL, group_id TEXT NOT NULL DEFAULT '', date TEXT NOT NULL,
                      character_name TEXT, image_url TEXT, source TEXT, extra TEXT,
                      change_count INTEGER NOT NULL DEFAULT 0,
                      PRIMARY KEY(sender_id, group_id, date));
                    """
                )
                await db.commit()
            self._initialized = True

    @staticmethod
    def scope_id(launcher_type: str, launcher_id: str, config: dict) -> str:
        return str(launcher_id) if str(config.get("leaderboard_scope", "global")) == "group" and launcher_type == "group" else ""

    async def _user(self, sender_id: str, scope_id: str):
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT points, streak, last_checkin_date, total_checkins, sender_name FROM users WHERE sender_id=? AND scope_id=?",
                (sender_id, scope_id),
            )
            return await cursor.fetchone()

    async def checkin(self, sender_id: str, scope_id: str, sender_name: str) -> str:
        await self._ensure_db()
        today = self.today()
        async with self._db_lock, aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute(
                "SELECT points, streak, last_checkin_date FROM users WHERE sender_id=? AND scope_id=?",
                (sender_id, scope_id),
            )
            row = await cursor.fetchone()
            if row and row[2] == today:
                await db.commit()
                return f"📅 今天已经签到过啦~\n当前累计积分：{row[0]}\n连续签到：{row[1]} 天\n明天再来吧！"
            streak = 1
            if row and row[2]:
                try:
                    if (datetime.fromisoformat(today) - datetime.fromisoformat(row[2])).days == 1:
                        streak = int(row[1]) + 1
                except ValueError:
                    pass
            tiers = self.tiers()
            tier = random.choices(tiers, weights=[t["weight"] for t in tiers], k=1)[0] if sum(t["weight"] for t in tiers) else random.choice(tiers)
            base = random.randint(tier["min_points"], tier["max_points"])
            base *= max(0, self._int("checkin_point_multiplier", 1))
            per_day, cap = self._int("streak_bonus_per_day", 50), self._int("streak_bonus_cap", 500)
            bonus = min(streak * per_day, cap) if per_day > 0 else 0
            gain = base + bonus
            await db.execute(
                "INSERT INTO users(sender_id,scope_id,points,streak,last_checkin_date,total_checkins,sender_name) VALUES(?,?,?,?,?,1,?) "
                "ON CONFLICT(sender_id,scope_id) DO UPDATE SET points=points+excluded.points,streak=excluded.streak,last_checkin_date=excluded.last_checkin_date,total_checkins=total_checkins+1,sender_name=excluded.sender_name",
                (sender_id, scope_id, gain, streak, today, sender_name),
            )
            await db.commit()
        total = (row[0] if row else 0) + gain
        if tier["name"] == "超大吉":
            title = "# 🌟 超大吉！终极大奖降临！"
        else:
            mood = "🎉" if "吉" in tier["name"] else "😢"
            title = f"# 📅 今日运势：{tier['name']} {mood}"
        lines = [
            title,
            f"**签到获得：** {base:,} 积分",
            f"**连签奖励：** +{bonus:,} 积分（连续第 {streak} 天）",
            "---",
            f"**当前累计：** {total:,} 积分",
            f"**连续签到：** 🔥 {streak} 天",
        ]
        return "\n".join(lines)

    async def my_info(self, sender_id: str, scope_id: str, group_id: str, sender_name: str) -> str:
        user = await self._user(sender_id, scope_id)
        wife = await self._wife(sender_id, group_id, self.today())
        lines = [f"# 👤 {sender_name} 的信息", f"**累计积分：** {user[0] if user else 0:,}",
                 f"**连续签到：** {user[1] if user else 0} 天", f"**总签到：** {user[3] if user else 0} 次"]
        lines.append(f"**💞 今日老婆：** {wife[0] or '神秘老婆'}" if wife else "**💌 今日老婆：** 还没抽，快来抽一位吧！")
        return "\n".join(lines)

    async def leaderboard(self, scope_id: str) -> str:
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT sender_id,sender_name,points FROM users WHERE scope_id=? ORDER BY points DESC LIMIT 10", (scope_id,))
            rows = await cursor.fetchall()
        if not rows:
            return "# 🏆 积分排行榜\n\n暂无排行数据，快去签到吧~"
        lines = [f"# 🏆 {'本群' if scope_id else '全局'}积分排行榜 Top10"]
        medals = ["🥇", "🥈", "🥉"]
        lines.extend(f"{medals[i] if i < 3 else str(i + 1) + '.'} **{name or uid}** — {points:,} 积分" for i, (uid, name, points) in enumerate(rows))
        return "\n".join(lines)

    async def _wife(self, sender_id: str, group_id: str, today: str):
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT character_name,image_url,source,extra,change_count FROM daily_wife WHERE sender_id=? AND group_id=? AND date=?", (sender_id, group_id, today))
            return await cursor.fetchone()

    async def draw(self) -> dict | None:
        if self.config.get("waifu_source", "manshuo") == "local":
            raw = self.config.get("local_wife_paths", "[]")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raw = [line.strip() for line in raw.splitlines() if line.strip()]
            files: list[Path] = []
            for item in raw if isinstance(raw, list) else []:
                path = Path(str(item)).expanduser()
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    files.append(path)
                elif path.is_dir():
                    files.extend(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
            if not files:
                return None
            image = random.choice(files).resolve()
            name = image.stem if self.config.get("local_wife_name_from_filename", True) else ""
            return {"name": name, "image": str(image), "source": "本地图库", "local": True}

        image_url = "https://web.manshuo.ink/api/img/today_wife"
        image_path = self.data_dir / "wife_images" / f"{uuid4().hex}.jpg"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(image_url, headers={"Accept": "image/*"})
                response.raise_for_status()
                if not response.headers.get("content-type", "").startswith("image/"):
                    return None
                image_path.write_bytes(response.content)
            return {"name": "", "image": str(image_path), "source": "漫朔", "local": True}
        except (httpx.HTTPError, OSError):
            image_path.unlink(missing_ok=True)
            return None

    async def wife(self, sender_id: str, group_id: str, sender_name: str):
        today = self.today()
        existing = await self._wife(sender_id, group_id, today)
        if existing:
            cost, limit = self._int("change_wife_cost", 3000), self._int("change_wife_limit", 2)
            lines = [f"# 💞 {sender_name}，今天已经抽到老婆啦！", f"**🎴 今日老婆：** {existing[0] or '神秘老婆'}"]
            if limit > 0:
                lines.append(f"**🔄 今日已换：** {int(existing[4])}/{limit} 次")
            lines.append(f"想再抽一次？发送 **换老婆**（消耗 {cost} 积分）" if cost > 0 else "还想换一位？发送 **换老婆** 即可免费重抽")
            return {"name": existing[0] or "", "image": existing[1] or "", "source": existing[2] or "", "text": "\n".join(lines), "change_count": int(existing[4])}
        result = await self.draw()
        if not result:
            return {"text": "老婆召唤失败，请检查图源配置或稍后再试~"}
        await self._save_wife(sender_id, group_id, today, result, 0)
        cost, limit = self._int("change_wife_cost", 3000), self._int("change_wife_limit", 2)
        title = f"🎉 命运牵线成功！今天与你相伴的是：{result['name']}" if result.get("name") else "🎉 命运牵线成功！今天的专属老婆已送达！"
        text = [f"# {title}"]
        if limit > 0:
            text.append(f"**🔄 今日换老婆次数：** 0/{limit}")
        text.append(f"想重新抽取？发送 **换老婆**（消耗 {cost} 积分）" if cost > 0 else "想重新抽取？发送 **换老婆** 即可免费重抽")
        return {**result, "text": "\n".join(text), "change_count": 0}

    async def _save_wife(self, sender_id: str, group_id: str, today: str, result: dict, count: int):
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO daily_wife(sender_id,group_id,date,character_name,image_url,source,extra,change_count) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(sender_id,group_id,date) DO UPDATE SET character_name=excluded.character_name,image_url=excluded.image_url,source=excluded.source,extra=excluded.extra,change_count=excluded.change_count", (sender_id, group_id, today, result.get("name", ""), result.get("image", ""), result.get("source", ""), json.dumps(result, ensure_ascii=False), count))
            await db.commit()

    async def change_wife(self, sender_id: str, scope_id: str, group_id: str, sender_name: str):
        today = self.today()
        existing = await self._wife(sender_id, group_id, today)
        if not existing:
            return {"text": "# 还没有今日老婆\n\n先发送 **老婆** 抽一个吧~"}
        cost, limit, count = self._int("change_wife_cost", 3000), self._int("change_wife_limit", 2), int(existing[4])
        if limit > 0 and count >= limit:
            return {"text": f"# 换老婆次数已用完\n\n今日上限为 **{limit} 次**，明天再来吧~"}
        user = await self._user(sender_id, scope_id)
        points = user[0] if user else 0
        if cost > 0 and points < cost:
            return {"text": f"# 积分不足\n\n换老婆需要 **{cost:,} 积分**，你当前有 **{points:,} 积分**，还差 **{cost - points:,} 积分**。"}
        result = await self.draw()
        if not result:
            return {"text": "# 老婆召唤失败\n\n请检查图源配置或稍后再试~"}
        await self._ensure_db()
        async with self._db_lock, aiosqlite.connect(self.db_path) as db:
            await db.execute("BEGIN IMMEDIATE")
            cursor = await db.execute("SELECT points FROM users WHERE sender_id=? AND scope_id=?", (sender_id, scope_id))
            balance = await cursor.fetchone()
            if cost > 0 and (not balance or balance[0] < cost):
                await db.rollback()
                current = balance[0] if balance else 0
                return {"text": f"# 积分不足\n\n换老婆需要 **{cost:,} 积分**，你当前有 **{current:,} 积分**，还差 **{cost - current:,} 积分**。"}
            if cost > 0:
                await db.execute("UPDATE users SET points=points-?,sender_name=? WHERE sender_id=? AND scope_id=?", (cost, sender_name, sender_id, scope_id))
            await db.execute("INSERT INTO daily_wife(sender_id,group_id,date,character_name,image_url,source,extra,change_count) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(sender_id,group_id,date) DO UPDATE SET character_name=excluded.character_name,image_url=excluded.image_url,source=excluded.source,extra=excluded.extra,change_count=excluded.change_count", (sender_id, group_id, today, result.get("name", ""), result.get("image", ""), result.get("source", ""), json.dumps(result, ensure_ascii=False), count + 1))
            await db.commit()
        prefix = f"🔄 换老婆成功（消耗 {cost} 积分）" if cost > 0 else "🔄 换老婆成功"
        title = f"💘 {prefix}！新老婆是：{result.get('name')}" if result.get("name") else f"💘 {prefix}！新老婆已到位！"
        lines = [f"# {title}"]
        if limit > 0:
            lines.append(f"**🔄 今日换老婆次数：** {count + 1}/{limit}")
        user_after = await self._user(sender_id, scope_id)
        if user_after:
            lines.append(f"**💰 剩余积分：** {user_after[0]:,}")
        return {**result, "text": "\n".join(lines)}
