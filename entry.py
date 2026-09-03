from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json

from workers import WorkerEntrypoint, Response
from js import fetch, Object
from pyodide.ffi import to_js


def js_options(options):
    return to_js(options, dict_converter=Object.fromEntries)


async def telegram_call(token, method, data):
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(data, ensure_ascii=False)

    response = await fetch(
        url,
        js_options({
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": body,
        }),
    )
    return await response.json()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Telegram webhook endpoint
        if request.method == "POST":
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            expected = getattr(self.env, "WEBHOOK_SECRET", "")

            if expected and secret != expected:
                return Response("Unauthorized", status=401)

            try:
                update = await request.json()
            except Exception:
                return Response("Bad Request", status=400)

            message = update.get("message", {})
            chat = message.get("chat", {})
            text = message.get("text", "")

            if not chat.get("id"):
                return Response("OK")

            if text == "/start":
                cairo = ZoneInfo("Africa/Cairo")
                now = datetime.now(timezone.utc).astimezone(cairo)
                current_time = now.strftime("%H:%M:%S")
                current_date = now.strftime("%Y-%m-%d")

                reply = (
                    "👋 أهلاً بك!\n\n"
                    f"🕐 الساعة الآن: {current_time}\n"
                    f"📅 التاريخ: {current_date}\n"
                    "🌍 التوقيت: Africa/Cairo (مصر)\n\n"
                    "👨‍💻 المطور: @MSR_Cracker"
                )

                await telegram_call(
                    self.env.BOT_TOKEN,
                    "sendMessage",
                    {
                        "chat_id": chat["id"],
                        "text": reply,
                    },
                )

            return Response("OK")

        return Response(
            "Telegram Time Bot is running.\n"
            "Developer: @MSR_Cracker"
        )
