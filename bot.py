# -*- coding: utf-8 -*-
import logging
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,
)

import config
import db
from lang import t

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Conversation states for withdrawal flow
ASK_AMOUNT, ASK_ADDRESS = range(2)


# ---------- Helpers ----------

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(t("menu_tasks", lang), callback_data="menu_tasks"),
         InlineKeyboardButton(t("menu_join_channel", lang), callback_data="menu_tasks")],
        [InlineKeyboardButton(t("menu_daily_bonus", lang), callback_data="daily_bonus"),
         InlineKeyboardButton(t("menu_referral", lang), callback_data="referral")],
        [InlineKeyboardButton(t("menu_balance", lang), callback_data="balance"),
         InlineKeyboardButton(t("menu_withdraw", lang), callback_data="withdraw_start")],
        [InlineKeyboardButton(t("menu_language", lang), callback_data="change_lang")],
    ]
    return InlineKeyboardMarkup(rows)


def lang_keyboard() -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton("دری", callback_data="setlang_fa"),
        InlineKeyboardButton("پښتو", callback_data="setlang_ps"),
        InlineKeyboardButton("English", callback_data="setlang_en"),
    ]]
    return InlineKeyboardMarkup(rows)


def user_lang(user_id: int) -> str:
    u = db.get_user(user_id)
    return u["lang"] if u else "en"


# ---------- /start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    existing = db.get_user(tg_user.id)

    referred_by = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                ref_id = int(arg.replace("ref_", ""))
                if ref_id != tg_user.id:
                    referred_by = ref_id
            except ValueError:
                pass

    if not existing:
        db.create_user(tg_user.id, tg_user.username or "", tg_user.first_name or "", referred_by)
        if referred_by and db.get_user(referred_by):
            db.add_points(referred_by, config.POINTS_REFERRAL)
            try:
                ref_lang = user_lang(referred_by)
                await context.bot.send_message(
                    referred_by,
                    "🎉 " + t("task_success", ref_lang, points=config.POINTS_REFERRAL)
                )
            except Exception:
                pass
        await update.message.reply_text(t("choose_language", "en"), reply_markup=lang_keyboard())
    else:
        lang = existing["lang"]
        await update.message.reply_text(
            t("welcome", lang, name=tg_user.first_name or ""),
            reply_markup=main_menu_keyboard(lang),
        )


async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace("setlang_", "")
    db.set_lang(query.from_user.id, lang_code)
    await query.edit_message_text(
        t("welcome", lang_code, name=query.from_user.first_name or ""),
    )
    await context.bot.send_message(
        query.from_user.id,
        t("welcome", lang_code, name=query.from_user.first_name or ""),
        reply_markup=main_menu_keyboard(lang_code),
    )


async def change_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(t("choose_language", "en"), reply_markup=lang_keyboard())


# ---------- Balance ----------

async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u = db.get_user(query.from_user.id)
    lang = u["lang"]
    usdt = round(u["points"] / config.POINTS_PER_USDT, 4)
    await query.message.reply_text(t("balance_msg", lang, points=u["points"], usdt=usdt))


# ---------- Daily Bonus ----------

async def daily_bonus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u = db.get_user(query.from_user.id)
    lang = u["lang"]
    now = int(time.time())
    if now - u["last_daily_bonus"] < 24 * 3600:
        await query.message.reply_text(t("daily_bonus_wait", lang))
        return
    db.add_points(u["user_id"], config.POINTS_DAILY_BONUS)
    db.set_last_daily_bonus(u["user_id"], now)
    await query.message.reply_text(t("daily_bonus_ok", lang, points=config.POINTS_DAILY_BONUS))


# ---------- Referral ----------

async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u = db.get_user(query.from_user.id)
    lang = u["lang"]
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{u['user_id']}"
    count = db.count_referrals(u["user_id"])
    await query.message.reply_text(
        t("referral_msg", lang, link=link, points=config.POINTS_REFERRAL, count=count)
    )


# ---------- Tasks (Join Channel) ----------

async def tasks_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_lang(query.from_user.id)
    tasks = db.get_active_tasks()
    if not tasks:
        await query.message.reply_text(t("no_tasks", lang))
        return
    for task in tasks:
        if db.has_completed_task(query.from_user.id, task["task_id"]):
            continue
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(t("verify_btn", lang), callback_data=f"verify_{task['task_id']}")
        ]])
        await query.message.reply_text(
            t("task_join_prompt", lang, channel=task["channel_display"] or task["channel_username"]),
            reply_markup=kb,
        )


async def verify_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = user_lang(query.from_user.id)
    task_id = int(query.data.replace("verify_", ""))

    with db.get_conn() as conn:
        row = conn.execute("SELECT * FROM channel_tasks WHERE task_id=?", (task_id,)).fetchone()
    if not row:
        await query.answer()
        return
    task = dict(row)

    if db.has_completed_task(query.from_user.id, task_id):
        await query.answer(t("task_already_done", lang), show_alert=True)
        return

    try:
        member = await context.bot.get_chat_member(task["channel_username"], query.from_user.id)
        joined = member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning(f"get_chat_member failed: {e}")
        joined = False

    if not joined:
        await query.answer(t("task_not_joined", lang), show_alert=True)
        return

    db.add_points(query.from_user.id, task["points"])
    db.mark_task_completed(query.from_user.id, task_id)
    await query.answer()
    await query.edit_message_text(t("task_success", lang, points=task["points"]))


# ---------- Withdraw Conversation ----------

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_lang(query.from_user.id)
    min_points = int(config.MIN_WITHDRAW_USDT * config.POINTS_PER_USDT)
    await query.message.reply_text(
        t("withdraw_ask_amount", lang, min_points=min_points, min_usdt=config.MIN_WITHDRAW_USDT)
    )
    return ASK_AMOUNT


async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text(t("invalid_number", lang))
        return ASK_AMOUNT

    points = int(text)
    min_points = int(config.MIN_WITHDRAW_USDT * config.POINTS_PER_USDT)
    u = db.get_user(update.effective_user.id)
    if points < min_points or points > u["points"]:
        await update.message.reply_text(t("withdraw_too_low", lang))
        return ConversationHandler.END

    context.user_data["withdraw_points"] = points
    await update.message.reply_text(t("withdraw_ask_address", lang))
    return ASK_ADDRESS


async def withdraw_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    address = update.message.text.strip()
    points = context.user_data.get("withdraw_points")

    if not points or not db.deduct_points(update.effective_user.id, points):
        await update.message.reply_text(t("withdraw_too_low", lang))
        return ConversationHandler.END

    usdt = round(points / config.POINTS_PER_USDT, 4)
    req_id = db.create_withdrawal(update.effective_user.id, points, usdt, address)
    await update.message.reply_text(t("withdraw_submitted", lang, req_id=req_id))

    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                t("admin_new_withdraw", "en", user_id=update.effective_user.id,
                  usdt=usdt, points=points, address=address, req_id=req_id),
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")

    return ConversationHandler.END


async def withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(t("cancelled", lang))
    return ConversationHandler.END


# ---------- Admin Commands ----------

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def admin_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /addtask @channelusername Display Name | points"""
    if not is_admin(update.effective_user.id):
        return
    try:
        raw = update.message.text.split(maxsplit=1)[1]
        channel_part, points_part = raw.rsplit("|", 1)
        channel_part = channel_part.strip()
        points = int(points_part.strip())
        if " " in channel_part:
            username, display = channel_part.split(" ", 1)
        else:
            username, display = channel_part, channel_part
        task_id = db.add_channel_task(username.strip(), display.strip(), points)
        await update.message.reply_text(f"✅ Task #{task_id} added: {username} ({points} pts)")
    except Exception:
        await update.message.reply_text(
            "Usage:\n/addtask @channelusername Display Name | points\n"
            "Example:\n/addtask @mychannel My Channel | 50"
        )


async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /approve <req_id>"""
    if not is_admin(update.effective_user.id):
        return
    try:
        req_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /approve <req_id>")
        return
    w = db.get_withdrawal(req_id)
    if not w or w["status"] != "pending":
        await update.message.reply_text("Request not found or already processed.")
        return
    db.set_withdrawal_status(req_id, "approved")
    lang = user_lang(w["user_id"])
    await context.bot.send_message(w["user_id"], t("withdraw_approved_user", lang, req_id=req_id))
    await update.message.reply_text(f"✅ Approved #{req_id}. Now send {w['usdt']} USDT to {w['address']} manually.")


async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /reject <req_id>"""
    if not is_admin(update.effective_user.id):
        return
    try:
        req_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /reject <req_id>")
        return
    w = db.get_withdrawal(req_id)
    if not w or w["status"] != "pending":
        await update.message.reply_text("Request not found or already processed.")
        return
    db.set_withdrawal_status(req_id, "rejected")
    db.add_points(w["user_id"], w["points"])  # refund
    lang = user_lang(w["user_id"])
    await context.bot.send_message(w["user_id"], t("withdraw_rejected_user", lang, req_id=req_id))
    await update.message.reply_text(f"❌ Rejected #{req_id}, points refunded to user.")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    with db.get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) c FROM withdrawals WHERE status='pending'").fetchone()["c"]
        total_points = conn.execute("SELECT SUM(points) s FROM users").fetchone()["s"] or 0
    await update.message.reply_text(
        f"👥 Users: {users}\n⏳ Pending withdrawals: {pending}\n💰 Total points in system: {total_points}"
    )


# ---------- Fallback ----------

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(t("welcome", lang, name=update.effective_user.first_name or ""),
                                     reply_markup=main_menu_keyboard(lang))


def main():
    db.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", back_to_menu))

    app.add_handler(CallbackQueryHandler(set_language_callback, pattern="^setlang_"))
    app.add_handler(CallbackQueryHandler(change_lang_callback, pattern="^change_lang$"))
    app.add_handler(CallbackQueryHandler(balance_callback, pattern="^balance$"))
    app.add_handler(CallbackQueryHandler(daily_bonus_callback, pattern="^daily_bonus$"))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(tasks_callback, pattern="^menu_tasks$"))
    app.add_handler(CallbackQueryHandler(verify_task_callback, pattern="^verify_"))

    withdraw_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_start, pattern="^withdraw_start$")],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_address)],
        },
        fallbacks=[CommandHandler("cancel", withdraw_cancel)],
    )
    app.add_handler(withdraw_conv)

    app.add_handler(CommandHandler("addtask", admin_add_task))
    app.add_handler(CommandHandler("approve", admin_approve))
    app.add_handler(CommandHandler("reject", admin_reject))
    app.add_handler(CommandHandler("stats", admin_stats))

    logger.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
