from datetime import datetime, timedelta, timezone
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
            "headers": {
                "Content-Type": "application/json",
            },
            "body": body,
        }),
    )

    return await response.json()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "POST":
            secret = request.headers.get(
                "X-Telegram-Bot-Api-Secret-Token"
            )
            expected = getattr(
                self.env,
                "WEBHOOK_SECRET",
                ""
            )

            if expected and secret != expected:
                return Response("Unauthorized", status=401)

            try:
                update = await request.json()
            except Exception:
                return Response("Bad Request", status=400)

            message = update.get("message") or {}
            chat = message.get("chat") or {}
            text = message.get("text") or ""

            chat_id = chat.get("id")

            if not chat_id:
                return Response("OK")

            if text == "/start":
                # Egypt time: UTC+3 during daylight saving time
                egypt_tz = timezone(timedelta(hours=3))
                now = datetime.now(timezone.utc).astimezone(egypt_tz)

                current_time = now.strftime("%H:%M:%S")
                current_date = now.strftime("%Y-%m-%d")

                reply = (
                    "👋 أهلاً بك!\n\n"
                    f"🕐 الساعة الآن: {current_time}\n"
                    f"📅 التاريخ: {current_date}\n"
                    "🌍 التوقيت: Africa/Cairo (مصر)\n\n"
                    "👨‍💻 المطور: @MSR_Cracker"
                )

                result = await telegram_call(
                    self.env.BOT_TOKEN,
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": reply,
                    },
                )

                if not result.get("ok"):
                    return Response(
                        "Telegram API Error",
                        status=500
                    )

            return Response("OK")

        return Response(
            "Telegram Time Bot is running.\n"
            "Developer: @MSR_Cracker"
        )
