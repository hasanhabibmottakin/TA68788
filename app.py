from flask import Flask, request, jsonify, Response
import requests, json, os, time
from datetime import datetime

app = Flask(__name__)

API_JSON = "api.json"

# ---- CACHE ----
cache = {
    "channels": {"data": None, "time": 0},
    "cookie_toffee": {"data": None, "time": 0},
    "cookie_epl": {"data": None, "time": 0},
}
CACHE_TTL = 3600   # 1 hour


# ---------- Cookie fetcher ----------
def fetch_cookie(playback_id):
    api_url = f"https://toffeelive.com/api/web/playback/{playback_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Authorization": "Bearer eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...",
        "Accept": "*/*",
        "Referer": "https://toffeelive.com/",
        "Origin": "https://toffeelive.com",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(api_url, headers=headers, json={}, allow_redirects=False, timeout=10)
        cookies = resp.cookies.get_dict()
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])
    except Exception:
        return None


def get_cookie(playback_id, key):
    now = time.time()
    if cache[key]["data"] and (now - cache[key]["time"] < CACHE_TTL):
        return cache[key]["data"]

    cookie = fetch_cookie(playback_id)
    if cookie:
        cache[key] = {"data": cookie, "time": now}
    return cookie


def load_channels():
    now = time.time()
    if cache["channels"]["data"] and (now - cache["channels"]["time"] < CACHE_TTL):
        return cache["channels"]["data"]

    if not os.path.exists(API_JSON):
        return []

    with open(API_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    cache["channels"] = {"data": data, "time": now}
    return data


# ---------- ROOT / ----------
@app.route("/")
def index():
    return jsonify({
        "message": "Toffee API - Available Endpoints , Made By: Bd Cooder Boy @fredflixceo",
        "available_routes": [
            "/cookie",
            "/ns",
            "/channels",
            "/ott",
            "/tengo",
            "/routes"
        ],
        "cache_ttl_seconds": CACHE_TTL,
        "last_cache_update": {
            "channels": cache["channels"]["time"],
            "cookie_toffee": cache["cookie_toffee"]["time"],
            "cookie_epl": cache["cookie_epl"]["time"]
        }
    })


# ---------- CMD HANDLER ----------
@app.route("/<cmd>")
def handler(cmd):
    channels = load_channels()
    if not channels:
        return jsonify({"error": "api.json not found"}), 404

    # cached cookies
    cookie_toffee = get_cookie("Ai51-JQBv9knK3AH_jWs", "cookie_toffee")
    cookie_epl = get_cookie("JS1AqZgBNnOkwJLWlwg-", "cookie_epl")

    if not cookie_toffee and not cookie_epl:
        return jsonify({"error": "Failed to fetch cookies"}), 500

    # assign cookies
    for ch in channels:
        if ch.get("category_name", "").lower() == "epl":
            ch["cookie"] = cookie_epl or cookie_toffee
        else:
            ch["cookie"] = cookie_toffee

    # -------- ENDPOINTS --------
    if cmd == "cookie":
        return jsonify({"toffee": cookie_toffee, "epl": cookie_epl})

    if cmd == "ns":
        return Response(json.dumps(channels, ensure_ascii=False, indent=2), mimetype="application/json")

    if cmd == "channels":
        final = {
            "name": "Toffee App All Channel Link with Headers",
            "owner": "BD Cooder Boy \nTelegram: https://t.me/fredflixceo",
            "channels_amount": len(channels),
            "updated_on": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            "channels": channels
        }
        return Response(json.dumps(final, ensure_ascii=False, indent=2), mimetype="application/json")

    if cmd == "ott":
        lines = ["#EXTM3U"]
        for ch in channels:
            lines.append(f'#EXTINF:-1 group-title="{ch.get("category_name","")}" tvg-logo="{ch.get("logo","")}", {ch.get("name","")}')
            lines.append('#EXTVLCOPT:http-user-agent=Toffee (Linux;Android 14)')
            if ch.get("cookie"):
                lines.append(f'#EXTHTTP:{{"cookie":"{ch["cookie"]}"}}')
            lines.append(ch.get("link",""))
            lines.append("")
        return Response("\n".join(lines), mimetype="text/plain")

    if cmd == "tengo":
        resp = {
            "name": "Toffee App All Channel Link with Headers",
            "owner": "Bd Coder Boy \nTelegram: https://t.me/fredflixceo",
            "channels_amount": len(channels),
            "updated_on": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
            "channels": []
        }
        for ch in channels:
            parsed_host = ""
            try:
                parsed_host = requests.utils.urlparse(ch.get("link","")).hostname or ""
            except Exception:
                pass
            resp["channels"].append({
                "category_name": ch.get("category_name",""),
                "name": ch.get("name",""),
                "link": ch.get("link",""),
                "headers": {
                    "Host": parsed_host,
                    "cookie": ch.get("cookie",""),
                    "user-agent": "Toffee (Linux;Android 14)",
                    "accept-encoding": "gzip"
                },
                "logo": ch.get("logo","")
            })
        return Response(json.dumps(resp, ensure_ascii=False, indent=2), mimetype="application/json")

    if cmd == "routes":
        return jsonify({
            "available_routes": [
                "/cookie",
                "/ns",
                "/channels",
                "/ott",
                "/tengo",
                "/routes"
            ],
            "cache_ttl_seconds": CACHE_TTL
        })

    return jsonify({"error": "Invalid or missing cmd"}), 400



