"""抓取 Steam 上一批游戏的当前在线人数,打印到终端。

用法: python fetch_players.py
"""

import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import sqlite3

import requests

KL = ZoneInfo("Asia/Kuala_Lumpur")

# Steam 的这个接口只返回人数,不返回游戏名,所以名字要自己维护。
# appid 去 steamdb.info 查,想换成自己关心的游戏就直接改这里。
GAMES = {
    730: "Counter-Strike 2",
    570: "Dota 2",
    578080: "PUBG: BATTLEGROUNDS",
    1172470: "Apex Legends",
    271590: "Grand Theft Auto V",
    1245620: "ELDEN RING",
    1086940: "Baldur's Gate 3",
    3764200: "Resident Evil 8",
    2050650: "Resident Evil 4",
    1462040: "FINAL FANTASY VII",
    1867240: "WARDOGS",
    431960: "Wallpaper Engine",
    550: "Left 4 Dead 2",
    105600: "Terraria",
    1203220: "NARAKA: BLADEPOINT",
}

URL = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"

def fetch_with_retry(app_id, attempts=3):
    """失败时重试,每次等待时间翻倍。"""
    for attempt in range(1, attempts + 1):
        try:
            return fetch_player_count(app_id)
        except requests.RequestException as error:
            if attempt == attempts:
                raise
            wait = 2 ** attempt          # 2 秒、4 秒
            print(f"    第 {attempt} 次失败,{wait} 秒后重试")
            time.sleep(wait)

def fetch_player_count(app_id):
    """返回该游戏当前在线人数;拿不到数据时返回 None。"""
    response = requests.get(URL, params={"appid": app_id}, timeout=10)
    response.raise_for_status()

    payload = response.json().get("response", {})

    # result == 1 才代表这次查询有效
    if payload.get("result") != 1:
        return None

    return payload.get("player_count")


def main():
    conn = init_db()
    fetched_at = datetime.now(timezone.utc)
    local_time = fetched_at.astimezone(KL)
    print(f"抓取时间: {local_time:%Y-%m-%d %H:%M:%S %Z}\n")

    ok = 0
    for app_id, name in GAMES.items():
        try:
            count = fetch_with_retry(app_id)
            status = "ok" if count is not None else "no_data"
        except requests.RequestException as error:
            count, status = None, "failed"
            print(f"  [失败] {name}: {error}")
        if status == "ok":
            print(f"  {name:<28} {count:>10,}")
            ok += 1
        elif status == "no_data":
            print(f"  [无数据] {name}")

        save(conn, app_id, name, count, status, fetched_at)
        time.sleep(1)

    print(f"\n成功 {ok} / {len(GAMES)}")

    conn.commit()
    conn.close()
    
def init_db(path="steam.db"):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_counts (
            ...
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS player_counts (
            id           INTEGER PRIMARY KEY,
            app_id       INTEGER NOT NULL,
            game_name    TEXT    NOT NULL,
            player_count INTEGER,
            fetched_at   TEXT    NOT NULL,
            status       TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn

def save(conn, app_id, game_name, count, status, fetched_at):
    conn.execute(
        """INSERT INTO player_counts
           (app_id, game_name, player_count, fetched_at, status)
           VALUES (?, ?, ?, ?, ?)""",
        (app_id, game_name, count, fetched_at.isoformat(), status),
    )

if __name__ == "__main__":
    main()