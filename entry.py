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


async def send_start(env, chat_id):
    egypt_tz = timezone(timedelta(hours=3))
    now = datetime.now(timezone.utc).astimezone(egypt_tz)

    reply = (
        "👋 أهلاً بك!\n\n"
        f"🕐 الساعة الآن: {now.strftime('%H:%M:%S')}\n"
        f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
        "🌍 التوقيت: Africa/Cairo (مصر)\n\n"
        "👨‍💻 المطور: @MSR_Cracker"
    )

    await telegram_call(
        env.BOT_TOKEN,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": reply,
        },
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "POST":
            try:
                update = await request.json()
            except Exception:
                return Response("Bad Request", status=400)

            message = update.get("message") or {}
            chat = message.get("chat") or {}
            text = message.get("text") or ""
            chat_id = chat.get("id")

            if chat_id and text == "/start":
                # إرسال الرسالة في الخلفية وعدم جعل Telegram ينتظرها
                self.ctx.waitUntil(
                    send_start(self.env, chat_id)
                )

            # الرد فورًا على Telegram
            return Response("OK", status=200)

        return Response(
            "Telegram Time Bot is running.\n"
            "Developer: @MSR_Cracker"
        )
