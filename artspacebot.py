#!/usr/bin/env python3
"""
artspacebot.py — Full-featured Telegram bot for ArtSpace.ai
Unlimited credits · keep-alive session · per-user settings

Set env vars or edit CREDS below:
  BOT_TOKEN          Telegram bot token
  ARTSPACE_EMAIL     artspace.ai email
  ARTSPACE_PASSWORD  artspace.ai password
"""

import asyncio
import logging
import os
import threading
from io import BytesIO
from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from artspace_api import ArtspaceClient, ArtspaceError, MODELS, PRESET_TYPES

# ── credentials ───────────────────────────────────────────────────────────────
BOT_TOKEN         = os.getenv("BOT_TOKEN",         "8737621732:AAGuhX1ocIh4FdHsCJSlE7CAkInzFvng6HM")
ARTSPACE_EMAIL    = os.getenv("ARTSPACE_EMAIL",    "fastplay80@gmail.com")
ARTSPACE_PASSWORD = os.getenv("ARTSPACE_PASSWORD", "andrea2021")

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
)
log = logging.getLogger("artspacebot")

# ── global keep-alive client ──────────────────────────────────────────────────
client = ArtspaceClient(auto_keepalive=True)

# ── per-user settings ─────────────────────────────────────────────────────────
DEFAULT_SETTINGS: dict = {
    "model":          "atomic-pro",
    "preset":         "raw",
    "width":          1024,
    "height":         1024,
    "enhance":        True,
    "content_filter": True,
    "negative":       "",
    "seed":           None,   # None = random each time
}
_user_settings: dict[int, dict] = {}
_ulock = threading.Lock()

def get_settings(uid: int) -> dict:
    with _ulock:
        if uid not in _user_settings:
            _user_settings[uid] = dict(DEFAULT_SETTINGS)
        return dict(_user_settings[uid])

def save_setting(uid: int, key: str, value) -> None:
    with _ulock:
        if uid not in _user_settings:
            _user_settings[uid] = dict(DEFAULT_SETTINGS)
        _user_settings[uid][key] = value

def reset_settings(uid: int) -> None:
    with _ulock:
        _user_settings[uid] = dict(DEFAULT_SETTINGS)

# ── conversation states ───────────────────────────────────────────────────────
WAIT_NEGATIVE, WAIT_SEED, WAIT_IMG2IMG_PHOTO, WAIT_IMG2IMG_PROMPT = range(4)

# ── size presets ──────────────────────────────────────────────────────────────
SIZE_PRESETS: dict[str, tuple[int, int]] = {
    "512×512":   (512,  512),
    "768×768":   (768,  768),
    "1024×1024": (1024, 1024),
    "1024×1312": (1024, 1312),
    "1312×1024": (1312, 1024),
    "832×1216":  (832,  1216),
    "1216×832":  (1216, 832),
}

# ─────────────────────────────────────────────────────────────────────────────
# keyboard / text helpers
# ─────────────────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape for MarkdownV2."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def settings_summary(s: dict) -> str:
    seed_str = str(s["seed"]) if s["seed"] is not None else "random"
    neg_str  = _esc(s["negative"]) if s["negative"] else "—"
    return (
        f"🤖 *Model:*    `{s['model']}`\n"
        f"🎨 *Preset:*   `{s['preset']}`\n"
        f"📐 *Size:*     `{s['width']}×{s['height']}`\n"
        f"✨ *Enhance:*  `{'on' if s['enhance'] else 'off'}`\n"
        f"🛡 *Filter:*   `{'on' if s['content_filter'] else 'off'}`\n"
        f"🚫 *Negative:* {neg_str}\n"
        f"🌱 *Seed:*     `{seed_str}`"
    )

def _settings_kb(s: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Model",    callback_data="menu:model"),
            InlineKeyboardButton("🎨 Preset",   callback_data="menu:preset"),
        ],
        [
            InlineKeyboardButton("📐 Size",     callback_data="menu:size"),
            InlineKeyboardButton(
                f"✨ Enhance {'✅' if s['enhance'] else '❌'}",
                callback_data=f"toggle:enhance:{int(not s['enhance'])}",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🛡 Filter {'✅' if s['content_filter'] else '❌'}",
                callback_data=f"toggle:filter:{int(not s['content_filter'])}",
            ),
            InlineKeyboardButton("🚫 Negative", callback_data="ask:negative"),
        ],
        [
            InlineKeyboardButton("🌱 Seed",     callback_data="ask:seed"),
            InlineKeyboardButton("🔄 Reset all", callback_data="reset:settings"),
        ],
        [InlineKeyboardButton("❌ Close",        callback_data="close:menu")],
    ])

def _model_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"set:model:{mid}")]
        for mid, label in MODELS.items()
    ]
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="back:settings")])
    return InlineKeyboardMarkup(rows)

def _preset_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(p.replace("-", " ").title(), callback_data=f"set:preset:{p}")]
        for p in PRESET_TYPES
    ]
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="back:settings")])
    return InlineKeyboardMarkup(rows)

def _size_kb() -> InlineKeyboardMarkup:
    items = list(SIZE_PRESETS.keys())
    rows  = []
    for i in range(0, len(items), 2):
        rows.append([
            InlineKeyboardButton(label, callback_data=f"set:size:{label}")
            for label in items[i:i+2]
        ])
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="back:settings")])
    return InlineKeyboardMarkup(rows)

# ─────────────────────────────────────────────────────────────────────────────
# /start  /help
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎨 *ArtSpace\\.ai Bot*\n\n"
        "Send any text to generate an image\\.\n\n"
        "*/gen* `<prompt>` — generate image\n"
        "*/img2img* — image\\-to\\-image\n"
        "*/settings* — model, size, style, seed\n"
        "*/history* \\[page\\] — your past generations\n"
        "*/credits* — account info\n"
        "*/help* — all commands",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *Commands*\n\n"
        "*/gen* `<prompt>` — generate \\(or just send text\\)\n"
        "*/img2img* — image\\-to\\-image workflow\n"
        "*/settings* — configure model, size, preset, seed\n"
        "*/history* \\[page\\] — browse past generations\n"
        "*/credits* — account \\& credit balance\n"
        "*/cancel* — cancel current operation\n\n"
        "⚙️ *Tips*\n"
        "• Negative prompt filters out unwanted elements\n"
        "• Lock a seed to reproduce exact images\n"
        "• Enhance rewrites your prompt with AI magic\n"
        "• Re\\-roll button under each image regenerates same prompt",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

# ─────────────────────────────────────────────────────────────────────────────
# core generation
# ─────────────────────────────────────────────────────────────────────────────

async def _do_generate(
    update: Update,
    ctx:    ContextTypes.DEFAULT_TYPE,
    prompt: str,
    image:  Optional[bytes] = None,
) -> None:
    uid  = update.effective_user.id
    s    = get_settings(uid)
    msg  = update.effective_message
    chat = update.effective_chat.id

    status = await msg.reply_text("⏳ Generating…")
    await ctx.bot.send_chat_action(chat, ChatAction.UPLOAD_PHOTO)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: client.generate(
                prompt,
                negative_prompt = s["negative"],
                seed            = s["seed"],
                width           = s["width"],
                height          = s["height"],
                model           = s["model"],
                enhance         = s["enhance"],
                image           = image,
                image_strength  = 35 if image else 20,
                content_filter  = s["content_filter"],
                preset_type     = s["preset"],
            ),
        )
    except ArtspaceError as exc:
        await status.edit_text(f"❌ Generation failed:\n`{_esc(str(exc))}`", parse_mode=ParseMode.MARKDOWN_V2)
        return
    except Exception as exc:
        await status.edit_text(f"❌ Unexpected error: `{_esc(str(exc))}`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    url = result.get("image_url")
    if not url:
        await status.edit_text("❌ No image URL returned\\. Try again\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    try:
        img_bytes = await loop.run_in_executor(None, lambda: client.download_image(url))
    except Exception as exc:
        await status.edit_text(
            f"⚠️ Generated but couldn't download:\n{_esc(url)}\n`{_esc(str(exc))}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    seed_used = result.get("seed") or s["seed"] or "random"
    caption = (
        f"✅ *Done\\!*\n"
        f"🌱 Seed: `{seed_used}`\n"
        f"🤖 `{result.get('model', s['model'])}`  🎨 `{s['preset']}`  📐 `{s['width']}×{s['height']}`"
    )

    # truncate prompt for callback_data (max 64 bytes total)
    reroll_prompt = prompt[:55].replace(":", "꞉")   # avoid colon collision in callback data

    await status.delete()
    await msg.reply_photo(
        photo        = BytesIO(img_bytes),
        caption      = caption,
        parse_mode   = ParseMode.MARKDOWN_V2,
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔁 Re-roll",    callback_data=f"reroll:{reroll_prompt}"),
            InlineKeyboardButton("📌 Lock seed",  callback_data=f"lockseed:{seed_used}"),
            InlineKeyboardButton("⚙️ Settings",   callback_data="back:settings"),
        ]]),
    )

# ─────────────────────────────────────────────────────────────────────────────
# /gen + plain-text
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_gen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = " ".join(ctx.args).strip() if ctx.args else ""
    if not prompt:
        await update.message.reply_text("Usage: /gen <your prompt here>")
        return
    await _do_generate(update, ctx, prompt)

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = (update.message.text or "").strip()
    if prompt:
        await _do_generate(update, ctx, prompt)

# ─────────────────────────────────────────────────────────────────────────────
# /img2img conversation
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_img2img(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📸 Send the *source image* to use as a base:",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return WAIT_IMG2IMG_PHOTO

async def img2img_got_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo
    doc   = update.message.document

    file_id = (photo[-1].file_id if photo
               else doc.file_id if doc and doc.mime_type and doc.mime_type.startswith("image/")
               else None)
    if not file_id:
        await update.message.reply_text("Please send a photo or image file.")
        return WAIT_IMG2IMG_PHOTO

    tg_file = await ctx.bot.get_file(file_id)
    buf = BytesIO()
    await tg_file.download_to_memory(buf)
    ctx.user_data["img2img_bytes"] = buf.getvalue()

    await update.message.reply_text(
        "✏️ Now send your *prompt* for this image:",
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return WAIT_IMG2IMG_PROMPT

async def img2img_got_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    prompt = (update.message.text or "").strip()
    image  = ctx.user_data.pop("img2img_bytes", None)
    if not image:
        await update.message.reply_text("Session lost — start over with /img2img")
        return ConversationHandler.END
    await _do_generate(update, ctx, prompt, image=image)
    return ConversationHandler.END

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────────────────────
# /settings + inline keyboard
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    s   = get_settings(uid)
    await update.message.reply_text(
        f"⚙️ *Settings*\n\n{settings_summary(s)}",
        parse_mode   = ParseMode.MARKDOWN_V2,
        reply_markup = _settings_kb(s),
    )
    return ConversationHandler.END

async def settings_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    q   = update.callback_query
    uid = q.from_user.id
    await q.answer()
    data = q.data

    # ── navigation ────────────────────────────────────────────────────────────
    if data == "close:menu":
        await q.message.delete()
        return ConversationHandler.END

    if data in ("back:settings", "menu:back"):
        s = get_settings(uid)
        try:
            await q.message.edit_text(
                f"⚙️ *Settings*\n\n{settings_summary(s)}",
                parse_mode   = ParseMode.MARKDOWN_V2,
                reply_markup = _settings_kb(s),
            )
        except Exception:
            pass
        return ConversationHandler.END

    if data == "menu:model":
        await q.message.edit_text("🤖 Choose model:", reply_markup=_model_kb())
        return ConversationHandler.END

    if data == "menu:preset":
        await q.message.edit_text("🎨 Choose preset:", reply_markup=_preset_kb())
        return ConversationHandler.END

    if data == "menu:size":
        await q.message.edit_text("📐 Choose size:", reply_markup=_size_kb())
        return ConversationHandler.END

    # ── mutations ─────────────────────────────────────────────────────────────
    if data.startswith("set:model:"):
        save_setting(uid, "model", data.split(":", 2)[2])

    elif data.startswith("set:preset:"):
        save_setting(uid, "preset", data.split(":", 2)[2])

    elif data.startswith("set:size:"):
        label = data[9:]
        w, h  = SIZE_PRESETS.get(label, (1024, 1024))
        save_setting(uid, "width",  w)
        save_setting(uid, "height", h)

    elif data.startswith("toggle:enhance:"):
        save_setting(uid, "enhance", bool(int(data.split(":")[-1])))

    elif data.startswith("toggle:filter:"):
        save_setting(uid, "content_filter", bool(int(data.split(":")[-1])))

    elif data == "reset:settings":
        reset_settings(uid)

    elif data == "ask:negative":
        ctx.user_data["settings_msg_id"] = q.message.message_id
        await q.message.reply_text(
            "🚫 Send your negative prompt \\(or `-` to clear\\):",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return WAIT_NEGATIVE

    elif data == "ask:seed":
        ctx.user_data["settings_msg_id"] = q.message.message_id
        await q.message.reply_text(
            "🌱 Send a seed number \\(or `-` for random each time\\):",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return WAIT_SEED

    elif data.startswith("reroll:"):
        prompt = data[7:].replace("꞉", ":")
        await _do_generate(update, ctx, prompt)
        return ConversationHandler.END

    elif data.startswith("lockseed:"):
        try:
            seed = int(data.split(":")[-1])
            save_setting(uid, "seed", seed)
            await q.message.reply_text(
                f"📌 Seed `{seed}` locked\\. Future generations will use this seed\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except (ValueError, IndexError):
            await q.answer("Couldn't parse seed.", show_alert=True)
        return ConversationHandler.END

    # refresh settings panel after any mutation
    s = get_settings(uid)
    try:
        await q.message.edit_text(
            f"⚙️ *Settings*\n\n{settings_summary(s)}",
            parse_mode   = ParseMode.MARKDOWN_V2,
            reply_markup = _settings_kb(s),
        )
    except Exception:
        pass
    return ConversationHandler.END

async def wait_negative(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    txt = (update.message.text or "").strip()
    save_setting(uid, "negative", "" if txt == "-" else txt)
    ctx.user_data.pop("awaiting", None)
    await update.message.reply_text(
        "✅ Negative prompt " + ("cleared\\." if txt == "-" else "saved\\."),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return ConversationHandler.END

async def wait_seed(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    txt = (update.message.text or "").strip()
    ctx.user_data.pop("awaiting", None)
    if txt == "-":
        save_setting(uid, "seed", None)
        await update.message.reply_text("🌱 Seed cleared \\(random\\)\\.", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        try:
            seed = int(txt)
            save_setting(uid, "seed", seed)
            await update.message.reply_text(
                f"🌱 Seed locked to `{seed}`\\.", parse_mode=ParseMode.MARKDOWN_V2
            )
        except ValueError:
            await update.message.reply_text("Invalid number — seed unchanged\\.", parse_mode=ParseMode.MARKDOWN_V2)
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────────────────────
# /history
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    page = 1
    if ctx.args:
        try:
            page = max(1, int(ctx.args[0]))
        except ValueError:
            pass

    msg    = update.effective_message
    status = await msg.reply_text(f"⏳ Loading history page {page}…")
    loop   = asyncio.get_event_loop()

    try:
        items = await loop.run_in_executor(None, lambda: client.get_history(page))
    except ArtspaceError as exc:
        await status.edit_text(f"❌ `{_esc(str(exc))}`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if not items:
        await status.edit_text("No history found for this page.")
        return

    await status.delete()

    # send up to 6 thumbnails as a media group
    media: list[InputMediaPhoto] = []
    for item in items[:6]:
        img_url = item.get("thumbnail") or item.get("image")
        if img_url:
            prompt_str = (item.get("prompt") or "")[:80]
            media.append(InputMediaPhoto(
                media   = img_url,
                caption = f"`{_esc(prompt_str)}`" if prompt_str else None,
                parse_mode = ParseMode.MARKDOWN_V2,
            ))
    if media:
        try:
            await ctx.bot.send_media_group(update.effective_chat.id, media=media)
        except Exception as exc:
            log.warning("media group failed: %s", exc)

    # nav buttons
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(f"◀ {page-1}", callback_data=f"histpage:{page-1}"))
    nav.append(InlineKeyboardButton(f"· {page} ·", callback_data="noop"))
    if len(items) >= 20:
        nav.append(InlineKeyboardButton(f"{page+1} ▶", callback_data=f"histpage:{page+1}"))

    await msg.reply_text(
        f"📜 *History* — page {page}  \\({len(items)} items\\)",
        parse_mode   = ParseMode.MARKDOWN_V2,
        reply_markup = InlineKeyboardMarkup([nav]),
    )

async def history_nav_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q    = update.callback_query
    await q.answer()
    if q.data == "noop":
        return
    page = int(q.data.split(":")[1])
    ctx.args = [str(page)]
    # reuse cmd_history — fake message ref
    class _FakeUpdate:
        effective_message = q.message
        effective_chat    = q.message.chat
        effective_user    = q.from_user
    await cmd_history(_FakeUpdate(), ctx)

# ─────────────────────────────────────────────────────────────────────────────
# /credits
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_credits(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    status = await update.message.reply_text("⏳ Fetching account info…")
    loop   = asyncio.get_event_loop()
    try:
        auth = await loop.run_in_executor(None, client._do_login)
    except Exception as exc:
        await status.edit_text(f"❌ `{_esc(str(exc))}`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    u     = auth.get("user", {})
    plan  = u.get("highest_plan", {})
    used  = u.get("credits_used", 0)
    total = plan.get("credits", 0)
    left  = "∞" if total > 10**15 else str(total - used)

    await status.edit_text(
        f"👤 *Account Info*\n\n"
        f"Name:   `{_esc(u.get('name', '?'))}`\n"
        f"Email:  `{_esc(u.get('email', '?'))}`\n"
        f"Plan:   `{_esc(plan.get('name', '?'))}`\n"
        f"Used:   `{used}`\n"
        f"Left:   `{left}`\n"
        f"Canvas: `{'yes' if u.get('can_access_canvas') else 'no'}`\n"
        f"Admin:  `{'yes' if u.get('is_admin') else 'no'}`",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

# ─────────────────────────────────────────────────────────────────────────────
# startup
# ─────────────────────────────────────────────────────────────────────────────

async def on_startup(app: Application) -> None:
    log.info("Logging into ArtSpace.ai …")
    loop = asyncio.get_event_loop()
    auth = await loop.run_in_executor(
        None, lambda: client.login(ARTSPACE_EMAIL, ARTSPACE_PASSWORD)
    )
    u = auth.get("user", {})
    log.info(
        "Logged in as %s — plan: %s — credits left: %s",
        u.get("email"),
        u.get("highest_plan", {}).get("name"),
        "∞" if u.get("highest_plan", {}).get("credits", 0) > 10**15 else "finite",
    )

# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("ERROR: BOT_TOKEN is empty.")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .post_init(on_startup)
        .build()
    )

    # ── img2img conversation ──────────────────────────────────────────────────
    img2img_conv = ConversationHandler(
        entry_points = [CommandHandler("img2img", cmd_img2img)],
        states = {
            WAIT_IMG2IMG_PHOTO:  [
                MessageHandler(
                    filters.PHOTO | (filters.Document.IMAGE),
                    img2img_got_photo,
                )
            ],
            WAIT_IMG2IMG_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, img2img_got_prompt)
            ],
        },
        fallbacks = [CommandHandler("cancel", cmd_cancel)],
        per_user  = True,
        allow_reentry = True,
    )

    # ── settings conversation ─────────────────────────────────────────────────
    settings_conv = ConversationHandler(
        entry_points = [
            CommandHandler("settings", cmd_settings),
            CallbackQueryHandler(
                settings_callback,
                pattern=r"^(menu:|set:|toggle:|ask:|reset:|back:|close:|reroll:|lockseed:)",
            ),
        ],
        states = {
            WAIT_NEGATIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_negative)],
            WAIT_SEED:     [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_seed)],
        },
        fallbacks = [CommandHandler("cancel", cmd_cancel)],
        per_user  = True,
        allow_reentry = True,
    )

    # ── register handlers ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("gen",     cmd_gen))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("credits", cmd_credits))
    app.add_handler(CommandHandler("cancel",  cmd_cancel))
    app.add_handler(img2img_conv)
    app.add_handler(settings_conv)
    app.add_handler(CallbackQueryHandler(history_nav_callback, pattern=r"^histpage:\d+$"))
    app.add_handler(CallbackQueryHandler(history_nav_callback, pattern=r"^noop$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("Bot started. Polling …")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
