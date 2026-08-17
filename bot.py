# -*- coding: utf-8 -*-

import logging
import os
import threading
import time

import httpx

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import config
import db

from lang import t
from webhook import flask_app


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# =========================================================
# CONVERSATION STATES
# =========================================================

ASK_AMOUNT, ASK_ADDRESS = range(2)


# =========================================================
# MAIN MENU
# =========================================================

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                t("menu_tasks", lang),
                callback_data="menu_tasks",
            ),
            InlineKeyboardButton(
                t("menu_join_channel", lang),
                callback_data="menu_tasks",
            ),
        ],

        [
            InlineKeyboardButton(
                t("menu_daily_bonus", lang),
                callback_data="daily_bonus",
            ),
            InlineKeyboardButton(
                t("menu_referral", lang),
                callback_data="referral",
            ),
        ],

        [
            InlineKeyboardButton(
                t("menu_balance", lang),
                callback_data="balance",
            ),
            InlineKeyboardButton(
                t("menu_withdraw", lang),
                callback_data="withdraw_start",
            ),
        ],

        [
            InlineKeyboardButton(
                t("menu_watch_ads", lang),
                callback_data="watch_ads",
            ),
        ],

        [
            InlineKeyboardButton(
                t("menu_support", lang),
                callback_data="support",
            ),
        ],

        [
            InlineKeyboardButton(
                t("menu_language", lang),
                callback_data="change_lang",
            ),
        ],
    ]

    return InlineKeyboardMarkup(rows)


# =========================================================
# LANGUAGE KEYBOARD
# =========================================================

def lang_keyboard() -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                "دری",
                callback_data="setlang_fa",
            ),
            InlineKeyboardButton(
                "پښتو",
                callback_data="setlang_ps",
            ),
            InlineKeyboardButton(
                "English",
                callback_data="setlang_en",
            ),
        ]
    ]

    return InlineKeyboardMarkup(rows)


# =========================================================
# USER LANGUAGE
# =========================================================

def user_lang(user_id: int) -> str:

    u = db.get_user(user_id)

    return u["lang"] if u else "en"


# =========================================================
# REQUIRED CHANNEL KEYBOARD
# =========================================================

def join_gate_keyboard(lang: str) -> InlineKeyboardMarkup:

    channel = (
        config.REQUIRED_CHANNEL
        or "@officialZORVAKChannel"
    )

    channel_username = channel.lstrip("@")

    channel_url = f"https://t.me/{channel_username}"

    rows = [
        [
            InlineKeyboardButton(
                t("join_channel_btn", lang),
                url=channel_url,
            )
        ],

        [
            InlineKeyboardButton(
                t("verify_join_btn", lang),
                callback_data="verify_required_join",
            )
        ],
    ]

    return InlineKeyboardMarkup(rows)


# =========================================================
# CHECK CHANNEL MEMBERSHIP
# =========================================================

async def is_joined_required_channel(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:

    channel = (
        config.REQUIRED_CHANNEL
        or "@officialZORVAKChannel"
    )

    try:

        member = await context.bot.get_chat_member(
            channel,
            user_id,
        )

        logger.info(
            "CHANNEL CHECK | channel=%s | user=%s | status=%s",
            channel,
            user_id,
            member.status,
        )

        return member.status in (
            "member",
            "administrator",
            "creator",
        )

    except Exception as e:

        logger.exception(
            "CHANNEL CHECK FAILED | channel=%s | user=%s | error=%s",
            channel,
            user_id,
            e,
        )

        return False


# =========================================================
# ENSURE USER JOINED
# =========================================================

async def ensure_joined(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:

    user_id = update.effective_user.id

    if await is_joined_required_channel(
        context,
        user_id,
    ):
        return True

    lang = user_lang(user_id)

    channel_display = (
        config.REQUIRED_CHANNEL_DISPLAY
        or config.REQUIRED_CHANNEL
        or "@officialZORVAKChannel"
    )

    message = t(
        "required_join_prompt",
        lang,
        channel=channel_display,
    )

    keyboard = join_gate_keyboard(lang)

    if update.callback_query:

        await update.callback_query.answer()

        await update.callback_query.message.reply_text(
            message,
            reply_markup=keyboard,
        )

    elif update.message:

        await update.message.reply_text(
            message,
            reply_markup=keyboard,
        )

    return False


# =========================================================
# VERIFY REQUIRED JOIN
# =========================================================

async def verify_required_join_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    user_id = query.from_user.id

    lang = user_lang(user_id)

    joined = await is_joined_required_channel(
        context,
        user_id,
    )

    if joined:

        await query.answer()

        await query.edit_message_text(
            t(
                "welcome",
                lang,
                name=query.from_user.first_name or "",
            )
        )

        await context.bot.send_message(
            user_id,
            t(
                "welcome",
                lang,
                name=query.from_user.first_name or "",
            ),
            reply_markup=main_menu_keyboard(lang),
        )

    else:

        await query.answer(
            t("still_not_joined", lang),
            show_alert=True,
        )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    tg_user = update.effective_user

    existing = db.get_user(tg_user.id)

    # -----------------------------------------------------
    # FORCE CHANNEL JOIN BEFORE BOT USAGE
    # -----------------------------------------------------

    if config.REQUIRED_CHANNEL:

        joined = await is_joined_required_channel(
            context,
            tg_user.id,
        )

        if not joined:

            lang = (
                existing["lang"]
                if existing
                else "en"
            )

            channel_display = (
                config.REQUIRED_CHANNEL_DISPLAY
                or config.REQUIRED_CHANNEL
            )

            await update.message.reply_text(
                t(
                    "required_join_prompt",
                    lang,
                    channel=channel_display,
                ),
                reply_markup=join_gate_keyboard(lang),
            )

            return

    # -----------------------------------------------------
    # REFERRAL
    # -----------------------------------------------------

    referred_by = None

    if context.args:

        arg = context.args[0]

        if arg.startswith("ref_"):

            try:

                ref_id = int(
                    arg.replace("ref_", "")
                )

                if ref_id != tg_user.id:
                    referred_by = ref_id

            except ValueError:
                pass

    # -----------------------------------------------------
    # NEW USER
    # -----------------------------------------------------

    if not existing:

        db.create_user(
            tg_user.id,
            tg_user.username or "",
            tg_user.first_name or "",
            referred_by,
        )

        if referred_by and db.get_user(referred_by):

            db.create_referral_pending(
                tg_user.id,
                referred_by,
            )

            uname = (
                f"@{tg_user.username}"
                if tg_user.username
                else "(no username)"
            )

            for admin_id in config.ADMIN_IDS:

                try:

                    keyboard = InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton(
                                "✅ Approve",
                                callback_data=(
                                    f"refapprove_{tg_user.id}"
                                ),
                            ),

                            InlineKeyboardButton(
                                "❌ Reject",
                                callback_data=(
                                    f"refreject_{tg_user.id}"
                                ),
                            ),
                        ]]
                    )

                    await context.bot.send_message(
                        admin_id,

                        f"👥 New referral pending approval\n"
                        f"New user: "
                        f"{tg_user.first_name or ''} "
                        f"{uname} "
                        f"(ID: {tg_user.id})\n"
                        f"Referred by: {referred_by}",

                        reply_markup=keyboard,
                    )

                except Exception as e:

                    logger.warning(
                        "Could not notify admin %s: %s",
                        admin_id,
                        e,
                    )

        await update.message.reply_text(
            t("choose_language", "en"),
            reply_markup=lang_keyboard(),
        )

        return

    # -----------------------------------------------------
    # EXISTING USER
    # -----------------------------------------------------

    lang = existing["lang"]

    await update.message.reply_text(
        t(
            "welcome",
            lang,
            name=tg_user.first_name or "",
        ),
        reply_markup=main_menu_keyboard(lang),
    )


# =========================================================
# SET LANGUAGE
# =========================================================

async def set_language_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    lang_code = query.data.replace(
        "setlang_",
        "",
    )

    db.set_lang(
        query.from_user.id,
        lang_code,
    )

    if not await is_joined_required_channel(
        context,
        query.from_user.id,
    ):

        channel_display = (
            config.REQUIRED_CHANNEL_DISPLAY
            or config.REQUIRED_CHANNEL
        )

        await query.edit_message_text(
            t(
                "required_join_prompt",
                lang_code,
                channel=channel_display,
            ),
            reply_markup=join_gate_keyboard(
                lang_code
            ),
        )

        return

    await query.edit_message_text(
        t(
            "welcome",
            lang_code,
            name=query.from_user.first_name or "",
        )
    )

    await context.bot.send_message(
        query.from_user.id,

        t(
            "welcome",
            lang_code,
            name=query.from_user.first_name or "",
        ),

        reply_markup=main_menu_keyboard(
            lang_code
        ),
    )


# =========================================================
# CHANGE LANGUAGE
# =========================================================

async def change_lang_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        t(
            "choose_language",
            "en",
        ),
        reply_markup=lang_keyboard(),
    )


# =========================================================
# BALANCE
# =========================================================

async def balance_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    u = db.get_user(
        query.from_user.id
    )

    lang = u["lang"]

    usdt = round(
        u["points"] /
        config.POINTS_PER_USDT,
        4,
    )

    await query.message.reply_text(
        t(
            "balance_msg",
            lang,
            points=u["points"],
            usdt=usdt,
        )
    )


# =========================================================
# DAILY BONUS
# =========================================================

async def daily_bonus_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    u = db.get_user(
        query.from_user.id
    )

    lang = u["lang"]

    now = int(time.time())

    if (
        now - u["last_daily_bonus"]
        < 24 * 3600
    ):

        await query.message.reply_text(
            t(
                "daily_bonus_wait",
                lang,
            )
        )

        return

    db.add_points(
        u["user_id"],
        config.POINTS_DAILY_BONUS,
    )

    db.set_last_daily_bonus(
        u["user_id"],
        now,
    )

    await query.message.reply_text(
        t(
            "daily_bonus_ok",
            lang,
            points=config.POINTS_DAILY_BONUS,
        )
    )


# =========================================================
# REFERRAL
# =========================================================

async def referral_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    u = db.get_user(
        query.from_user.id
    )

    lang = u["lang"]

    bot_username = (
        await context.bot.get_me()
    ).username

    link = (
        f"https://t.me/{bot_username}"
        f"?start=ref_{u['user_id']}"
    )

    count = db.count_referrals(
        u["user_id"]
    )

    await query.message.reply_text(
        t(
            "referral_msg",
            lang,
            link=link,
            points=config.POINTS_REFERRAL,
            count=count,
        )
    )


# =========================================================
# WATCH ADS
# =========================================================

async def watch_ads_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    lang = user_lang(user_id)

    # -----------------------------------------------------
    # CHECK ADSGRAM CONFIG
    # -----------------------------------------------------

    if (
        not getattr(config, "ADSGRAM_TOKEN", None)
        or not getattr(config, "ADSGRAM_BLOCK_ID", None)
    ):

        logger.error(
            "AdsGram configuration missing: "
            "ADSGRAM_TOKEN or ADSGRAM_BLOCK_ID"
        )

        await query.message.reply_text(
            t(
                "no_ads_available",
                lang,
            )
        )

        return

    # -----------------------------------------------------
    # CLEAN BLOCK ID
    # AdsGram requires numeric part only.
    # -----------------------------------------------------

    block_id = str(
        config.ADSGRAM_BLOCK_ID
    ).strip()

    if block_id.startswith("bot-"):

        block_id = block_id[4:]

    # -----------------------------------------------------
    # ADSGRAM API REQUEST
    # -----------------------------------------------------

    try:

        async with httpx.AsyncClient(
            timeout=10
        ) as client:

            response = await client.get(
                "https://api.adsgram.ai/advbot",

                params={
                    "tgid": user_id,
                    "blockid": block_id,
                    "language": lang,
                    "token": config.ADSGRAM_TOKEN,
                },
            )

        # -------------------------------------------------
        # LOG RESPONSE
        # -------------------------------------------------

        logger.info(
            "AdsGram response | status=%s | body=%s",
            response.status_code,
            response.text[:2000],
        )

        if response.status_code != 200:

            await query.message.reply_text(
                t(
                    "no_ads_available",
                    lang,
                )
            )

            return

        try:

            data = response.json()

        except ValueError:

            logger.error(
                "AdsGram returned invalid JSON: %s",
                response.text[:2000],
            )

            await query.message.reply_text(
                t(
                    "no_ads_available",
                    lang,
                )
            )

            return

    except Exception as e:

        logger.exception(
            "AdsGram request failed: %s",
            e,
        )

        await query.message.reply_text(
            t(
                "no_ads_available",
                lang,
            )
        )

        return

    # -----------------------------------------------------
    # EMPTY RESPONSE
    # -----------------------------------------------------

    if not data:

        logger.warning(
            "AdsGram returned empty response"
        )

        await query.message.reply_text(
            t(
                "no_ads_available",
                lang,
            )
        )

        return

    # -----------------------------------------------------
    # PARSE ADSGRAM RESPONSE
    # -----------------------------------------------------

    banner = data.get(
        "banner",
        data,
    )

    text_html = (
        banner.get("text_html")
        or banner.get("text")
        or ""
    )

    click_url = banner.get(
        "click_url"
    )

    button_name = (
        banner.get("button_name")
        or "Learn more"
    )

    image_url = banner.get(
        "image_url"
    )

    button_reward_name = (
        banner.get("button_reward_name")
        or t(
            "ad_watch_btn",
            lang,
        )
    )

    reward_url = banner.get(
        "reward_url"
    )

    # -----------------------------------------------------
    # KEYBOARD
    # -----------------------------------------------------

    keyboard_rows = []

    if click_url:

        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    button_name,
                    url=click_url,
                )
            ]
        )

    if reward_url:

        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    button_reward_name,
                    url=reward_url,
                )
            ]
        )

    # -----------------------------------------------------
    # NO BUTTON / NO AD
    # -----------------------------------------------------

    if not keyboard_rows:

        logger.warning(
            "AdsGram response contained no usable URLs: %s",
            data,
        )

        await query.message.reply_text(
            t(
                "no_ads_available",
                lang,
            )
        )

        return

    keyboard = InlineKeyboardMarkup(
        keyboard_rows
    )

    caption = (
        text_html
        or t(
            "ad_watch_prompt",
            lang,
            points=config.POINTS_AD_VIEW,
        )
    )

    # -----------------------------------------------------
    # SEND AD
    # -----------------------------------------------------

    try:

        if image_url:

            await query.message.reply_photo(
                photo=image_url,
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        else:

            await query.message.reply_text(
                caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:

        logger.exception(
            "Could not render AdsGram ad: %s",
            e,
        )

        await query.message.reply_text(
            caption,
            reply_markup=keyboard,
        )


# =========================================================
# AD REWARD
# =========================================================

async def ad_reward_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    user_id = query.from_user.id

    lang = user_lang(user_id)

    u = db.get_user(user_id)

    if not u:

        await query.answer(
            "User not found.",
            show_alert=True,
        )

        return

    now = int(time.time())

    last_ad_view = (
        u["last_ad_view"]
        or 0
    )

    elapsed = (
        now - last_ad_view
    )

    cooldown = (
        config.AD_VIEW_COOLDOWN_SECONDS
    )

    if elapsed < cooldown:

        remaining = (
            cooldown - elapsed
        )

        await query.answer(
            t(
                "ad_cooldown",
                lang,
                seconds=remaining,
            ),
            show_alert=True,
        )

        return

    # -----------------------------------------------------
    # REWARD
    # -----------------------------------------------------

    db.add_points(
        user_id,
        config.POINTS_AD_VIEW,
    )

    db.set_last_ad_view(
        user_id,
        now,
    )

    await query.answer()

    try:

        await query.edit_message_text(
            t(
                "ad_reward_ok",
                lang,
                points=config.POINTS_AD_VIEW,
            )
        )

    except Exception:

        await query.message.reply_text(
            t(
                "ad_reward_ok",
                lang,
                points=config.POINTS_AD_VIEW,
            )
        )


# =========================================================
# SUPPORT
# =========================================================

async def support_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    lang = user_lang(
        query.from_user.id
    )

    contact = (
        f"@{config.SUPPORT_USERNAME}"
        if config.SUPPORT_USERNAME
        else "-"
    )

    await query.message.reply_text(
        t(
            "support_msg",
            lang,
            contact=contact,
        )
    )


# =========================================================
# TASKS
# =========================================================

async def tasks_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    query = update.callback_query

    await query.answer()

    lang = user_lang(
        query.from_user.id
    )

    tasks = db.get_active_tasks()

    if not tasks:

        await query.message.reply_text(
            t(
                "no_tasks",
                lang,
            )
        )

        return

    for task in tasks:

        if db.has_completed_task(
            query.from_user.id,
            task["task_id"],
        ):
            continue

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    t("verify_btn", lang),
                    callback_data=(
                        f"verify_{task['task_id']}"
                    ),
                )
            ]]
        )

        await query.message.reply_text(
            t(
                "task_join_prompt",
                lang,
                channel=(
                    task["channel_display"]
                    or task["channel_username"]
                ),
            ),
            reply_markup=keyboard,
        )


# =========================================================
# VERIFY TASK
# =========================================================

async def verify_task_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    lang = user_lang(
        query.from_user.id
    )

    task_id = int(
        query.data.replace(
            "verify_",
            "",
        )
    )

    with db.get_conn() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM channel_tasks
            WHERE task_id=?
            """,
            (task_id,),
        ).fetchone()

    if not row:

        await query.answer()

        return

    task = dict(row)

    if db.has_completed_task(
        query.from_user.id,
        task_id,
    ):

        await query.answer(
            t(
                "task_already_done",
                lang,
            ),
            show_alert=True,
        )

        return

    try:

        member = await context.bot.get_chat_member(
            task["channel_username"],
            query.from_user.id,
        )

        joined = member.status in (
            "member",
            "administrator",
            "creator",
        )

    except Exception as e:

        logger.warning(
            "Task get_chat_member failed: %s",
            e,
        )

        joined = False

    if not joined:

        await query.answer(
            t(
                "task_not_joined",
                lang,
            ),
            show_alert=True,
        )

        return

    db.add_points(
        query.from_user.id,
        task["points"],
    )

    db.mark_task_completed(
        query.from_user.id,
        task_id,
    )

    await query.answer()

    await query.edit_message_text(
        t(
            "task_success",
            lang,
            points=task["points"],
        )
    )


# =========================================================
# WITHDRAW START
# =========================================================

async def withdraw_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):

        return ConversationHandler.END

    query = update.callback_query

    await query.answer()

    lang = user_lang(
        query.from_user.id
    )

    min_points = int(
        config.MIN_WITHDRAW_USDT
        * config.POINTS_PER_USDT
    )

    await query.message.reply_text(
        t(
            "withdraw_ask_amount",
            lang,
            min_points=min_points,
            min_usdt=config.MIN_WITHDRAW_USDT,
        )
    )

    return ASK_AMOUNT


# =========================================================
# WITHDRAW AMOUNT
# =========================================================

async def withdraw_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    lang = user_lang(
        update.effective_user.id
    )

    text = (
        update.message.text.strip()
    )

    if not text.isdigit():

        await update.message.reply_text(
            t(
                "invalid_number",
                lang,
            )
        )

        return ASK_AMOUNT

    points = int(text)

    min_points = int(
        config.MIN_WITHDRAW_USDT
        * config.POINTS_PER_USDT
    )

    u = db.get_user(
        update.effective_user.id
    )

    if (
        points < min_points
        or points > u["points"]
    ):

        await update.message.reply_text(
            t(
                "withdraw_too_low",
                lang,
            )
        )

        return ConversationHandler.END

    context.user_data[
        "withdraw_points"
    ] = points

    await update.message.reply_text(
        t(
            "withdraw_ask_address",
            lang,
        )
    )

    return ASK_ADDRESS


# =========================================================
# WITHDRAW ADDRESS
# =========================================================

async def withdraw_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    lang = user_lang(
        update.effective_user.id
    )

    address = (
        update.message.text.strip()
    )

    points = context.user_data.get(
        "withdraw_points"
    )

    if (
        not points
        or not db.deduct_points(
            update.effective_user.id,
            points,
        )
    ):

        await update.message.reply_text(
            t(
                "withdraw_too_low",
                lang,
            )
        )

        return ConversationHandler.END

    usdt = round(
        points /
        config.POINTS_PER_USDT,
        4,
    )

    req_id = db.create_withdrawal(
        update.effective_user.id,
        points,
        usdt,
        address,
    )

    await update.message.reply_text(
        t(
            "withdraw_submitted",
            lang,
            req_id=req_id,
        )
    )

    for admin_id in config.ADMIN_IDS:

        try:

            await context.bot.send_message(
                admin_id,

                t(
                    "admin_new_withdraw",
                    "en",
                    user_id=(
                        update.effective_user.id
                    ),
                    usdt=usdt,
                    points=points,
                    address=address,
                    req_id=req_id,
                ),
            )

        except Exception as e:

            logger.warning(
                "Could not notify admin: %s",
                e,
            )

    return ConversationHandler.END


# =========================================================
# CANCEL WITHDRAW
# =========================================================

async def withdraw_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    lang = user_lang(
        update.effective_user.id
    )

    await update.message.reply_text(
        t(
            "cancelled",
            lang,
        )
    )

    return ConversationHandler.END


# =========================================================
# REFERRAL APPROVE
# =========================================================

async def referral_approve_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer()

        return

    referred_id = int(
        query.data.replace(
            "refapprove_",
            "",
        )
    )

    ref = db.get_referral(
        referred_id
    )

    if (
        not ref
        or ref["status"] != "pending"
    ):

        await query.answer(
            "Already processed or not found.",
            show_alert=True,
        )

        return

    db.set_referral_status(
        referred_id,
        "approved",
    )

    db.add_points(
        ref["referrer_id"],
        config.POINTS_REFERRAL,
    )

    await query.answer(
        "Approved ✅"
    )

    await query.edit_message_text(
        query.message.text
        + "\n\n✅ APPROVED"
    )

    try:

        ref_lang = user_lang(
            ref["referrer_id"]
        )

        await context.bot.send_message(
            ref["referrer_id"],

            "🎉 "
            + t(
                "task_success",
                ref_lang,
                points=config.POINTS_REFERRAL,
            ),
        )

    except Exception as e:

        logger.warning(
            "Could not notify referrer: %s",
            e,
        )


# =========================================================
# REFERRAL REJECT
# =========================================================

async def referral_reject_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer()

        return

    referred_id = int(
        query.data.replace(
            "refreject_",
            "",
        )
    )

    ref = db.get_referral(
        referred_id
    )

    if (
        not ref
        or ref["status"] != "pending"
    ):

        await query.answer(
            "Already processed or not found.",
            show_alert=True,
        )

        return

    db.set_referral_status(
        referred_id,
        "rejected",
    )

    await query.answer(
        "Rejected ❌"
    )

    await query.edit_message_text(
        query.message.text
        + "\n\n❌ REJECTED"
    )


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(
    user_id: int,
) -> bool:

    return user_id in config.ADMIN_IDS


# =========================================================
# ADMIN ADD TASK
# =========================================================

async def admin_add_task(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    try:

        raw = update.message.text.split(
            maxsplit=1
        )[1]

        channel_part, points_part = raw.rsplit(
            "|",
            1,
        )

        channel_part = (
            channel_part.strip()
        )

        points = int(
            points_part.strip()
        )

        if " " in channel_part:

            username, display = (
                channel_part.split(
                    " ",
                    1,
                )
            )

        else:

            username = channel_part
            display = channel_part

        task_id = db.add_channel_task(
            username.strip(),
            display.strip(),
            points,
        )

        await update.message.reply_text(
            f"✅ Task #{task_id} added: "
            f"{username} ({points} pts)"
        )

    except Exception:

        await update.message.reply_text(
            "Usage:\n"
            "/addtask @username Display Name | points\n\n"
            "Example:\n"
            "/addtask @mychannel My Channel | 50\n"
            "/addtask @mygroup My Group | 50"
        )


# =========================================================
# ADMIN APPROVE WITHDRAW
# =========================================================

async def admin_approve(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    try:

        req_id = int(
            context.args[0]
        )

    except (IndexError, ValueError):

        await update.message.reply_text(
            "Usage: /approve <req_id>"
        )

        return

    w = db.get_withdrawal(
        req_id
    )

    if (
        not w
        or w["status"] != "pending"
    ):

        await update.message.reply_text(
            "Request not found or already processed."
        )

        return

    db.set_withdrawal_status(
        req_id,
        "approved",
    )

    lang = user_lang(
        w["user_id"]
    )

    await context.bot.send_message(
        w["user_id"],

        t(
            "withdraw_approved_user",
            lang,
            req_id=req_id,
        ),
    )

    await update.message.reply_text(
        f"✅ Approved #{req_id}. "
        f"Now send {w['usdt']} USDT "
        f"to {w['address']} manually."
    )


# =========================================================
# ADMIN REJECT
# =========================================================

async def admin_reject(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    try:

        req_id = int(
            context.args[0]
        )

    except (IndexError, ValueError):

        await update.message.reply_text(
            "Usage: /reject <req_id>"
        )

        return

    w = db.get_withdrawal(
        req_id
    )

    if (
        not w
        or w["status"] != "pending"
    ):

        await update.message.reply_text(
            "Request not found or already processed."
        )

        return

    db.set_withdrawal_status(
        req_id,
        "rejected",
    )

    db.add_points(
        w["user_id"],
        w["points"],
    )

    lang = user_lang(
        w["user_id"]
    )

    await context.bot.send_message(
        w["user_id"],

        t(
            "withdraw_rejected_user",
            lang,
            req_id=req_id,
        ),
    )

    await update.message.reply_text(
        f"❌ Rejected #{req_id}, "
        f"points refunded to user."
    )


# =========================================================
# ADMIN STATS
# =========================================================

async def admin_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_admin(
        update.effective_user.id
    ):
        return

    with db.get_conn() as conn:

        users = conn.execute(
            "SELECT COUNT(*) c FROM users"
        ).fetchone()["c"]

        pending = conn.execute(
            """
            SELECT COUNT(*) c
            FROM withdrawals
            WHERE status='pending'
            """
        ).fetchone()["c"]

        total_points = conn.execute(
            """
            SELECT SUM(points) s
            FROM users
            """
        ).fetchone()["s"] or 0

    await update.message.reply_text(
        f"👥 Users: {users}\n"
        f"⏳ Pending withdrawals: {pending}\n"
        f"💰 Total points: {total_points}"
    )


# =========================================================
# BACK TO MENU
# =========================================================

async def back_to_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await ensure_joined(
        update,
        context,
    ):
        return

    lang = user_lang(
        update.effective_user.id
    )

    await update.message.reply_text(
        t(
            "welcome",
            lang,
            name=(
                update.effective_user.first_name
                or ""
            ),
        ),
        reply_markup=main_menu_keyboard(
            lang
        ),
    )


# =========================================================
# FLASK SERVER
# =========================================================

def run_flask_server():

    port = int(
        os.environ.get(
            "PORT",
            8080,
        )
    )

    flask_app.run(
        host="0.0.0.0",
        port=port,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    # Initialize database
    db.init_db()

    # Start Flask
    flask_thread = threading.Thread(
        target=run_flask_server,
        daemon=True,
    )

    flask_thread.start()

    # Build Telegram application
    app = (
        Application
        .builder()
        .token(config.BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "menu",
            back_to_menu,
        )
    )

    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            set_language_callback,
            pattern="^setlang_",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            change_lang_callback,
            pattern="^change_lang$",
        )
    )

    # -----------------------------------------------------
    # MAIN MENU CALLBACKS
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            balance_callback,
            pattern="^balance$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            daily_bonus_callback,
            pattern="^daily_bonus$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            referral_callback,
            pattern="^referral$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            tasks_callback,
            pattern="^menu_tasks$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            verify_required_join_callback,
            pattern="^verify_required_join$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            watch_ads_callback,
            pattern="^watch_ads$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            support_callback,
            pattern="^support$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            ad_reward_callback,
            pattern="^ad_reward$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            verify_task_callback,
            pattern="^verify_",
        )
    )

    # -----------------------------------------------------
    # REFERRAL ADMIN
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            referral_approve_callback,
            pattern="^refapprove_",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            referral_reject_callback,
            pattern="^refreject_",
        )
    )

    # -----------------------------------------------------
    # WITHDRAW CONVERSATION
    # -----------------------------------------------------

    withdraw_conv = ConversationHandler(

        entry_points=[
            CallbackQueryHandler(
                withdraw_start,
                pattern="^withdraw_start$",
            )
        ],

        states={

            ASK_AMOUNT: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    withdraw_amount,
                )
            ],

            ASK_ADDRESS: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND,
                    withdraw_address,
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                withdraw_cancel,
            )
        ],
    )

    app.add_handler(
        withdraw_conv
    )

    # -----------------------------------------------------
    # ADMIN COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "addtask",
            admin_add_task,
        )
    )

    app.add_handler(
        CommandHandler(
            "approve",
            admin_approve,
        )
    )

    app.add_handler(
        CommandHandler(
            "reject",
            admin_reject,
        )
    )

    app.add_handler(
        CommandHandler(
            "stats",
            admin_stats,
        )
    )

    # -----------------------------------------------------
    # START BOT
    # -----------------------------------------------------

    logger.info(
        "Bot started successfully."
    )

    logger.info(
        "Required channel: %s",
        getattr(
            config,
            "REQUIRED_CHANNEL",
            None,
        ),
    )

    logger.info(
        "AdsGram configured: token=%s block=%s",
        bool(
            getattr(
                config,
                "ADSGRAM_TOKEN",
                None,
            )
        ),
        getattr(
            config,
            "ADSGRAM_BLOCK_ID",
            None,
        ),
    )

    app.run_polling()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

"config.py" کې دا حتماً تنظیم کړه

REQUIRED_CHANNEL = "@officialZORVAKChannel"
REQUIRED_CHANNEL_DISPLAY = "@officialZORVAKChannel"


ADSGRAM_TOKEN = "f5e051b500fc4e82a0d62dcb1ce56ebb"
