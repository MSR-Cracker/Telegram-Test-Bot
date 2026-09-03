from datetime import datetime, timedelta, timezone
import json

from workers import WorkerEntrypoint, Response
from js import fetch, Object
from pyodide.ffi import to_js


def js_options(options):
    return to_js(options, dict_converter=Object.fromEntries)


async def telegram_call(token, method, data):
    url = f"https://api.telegram.org/bot{token}/{method}"

    response = await fetch(
        url,
        js_options({
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(data, ensure_ascii=False),
        }),
    )

    return await response.json()


class Default(WorkerEntrypoint):

    async def fetch(self, request):

        if request.method != "POST":
            return Response(
                "Telegram Time Bot is running.\n"
                "Developer: @MSR_Cracker",
                status=200
            )

        try:
            update = await request.json()

            message = update.get("message") or {}
            chat = message.get("chat") or {}

            chat_id = chat.get("id")
            text = message.get("text") or ""

            if not chat_id:
                return Response("OK", status=200)

            if text == "/start":

                egypt_tz = timezone(timedelta(hours=3))
                now = datetime.now(timezone.utc).astimezone(egypt_tz)

                reply = (
                    "👋 أهلاً بك!\n\n"
                    f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n"
                    f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
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

                print("Telegram API:", json.dumps(result))

            return Response("OK", status=200)

        except Exception as e:
            print("ERROR:", str(e))
            return Response("OK", status=200)
