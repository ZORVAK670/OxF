# -*- coding: utf-8 -*-
# Translations: fa = Dari (Farsi/Persian), ps = Pashto, en = English

TEXTS = {
    "choose_language": {
        "fa": "لطفاً زبان خود را انتخاب کنید:",
        "ps": "مهرباني وکړئ ژبه غوره کړئ:",
        "en": "Please choose your language:",
    },
    "welcome": {
        "fa": "به ربات کسب درآمد خوش آمدید، {name}!\n\nاز منوی زیر استفاده کنید:",
        "ps": "تاسو ته ښه راغلاست، {name}!\n\nد لاندې مینو څخه کار واخلئ:",
        "en": "Welcome, {name}!\n\nUse the menu below:",
    },
    "menu_tasks": {"fa": "📝 وظایف", "ps": "📝 ټاسکونه", "en": "📝 Tasks"},
    "menu_join_channel": {"fa": "📺 عضویت در کانال", "ps": "📺 چینل جوائن", "en": "📺 Join Channel"},
    "menu_daily_bonus": {"fa": "🎁 جایزه روزانه", "ps": "🎁 ورځنی بونس", "en": "🎁 Daily Bonus"},
    "menu_referral": {"fa": "👥 دعوت از دوستان", "ps": "👥 ریفرل", "en": "👥 Referral"},
    "menu_balance": {"fa": "💰 موجودی", "ps": "💰 بیلانس", "en": "💰 Balance"},
    "menu_withdraw": {"fa": "💵 برداشت", "ps": "💵 وتل", "en": "💵 Withdraw"},
    "menu_language": {"fa": "🌐 تغییر زبان", "ps": "🌐 د ژبې بدلون", "en": "🌐 Change Language"},

    "balance_msg": {
        "fa": "💰 موجودی شما: {points} امتیاز\n(معادل تقریبی: {usdt} USDT)",
        "ps": "💰 ستاسو بیلانس: {points} امتیاز\n(نږدې معادل: {usdt} USDT)",
        "en": "💰 Your balance: {points} points\n(approx. equal to: {usdt} USDT)",
    },

    "daily_bonus_ok": {
        "fa": "🎁 تبریک! {points} امتیاز روزانه شما اضافه شد.",
        "ps": "🎁 مبارک شه! ستاسو ورځني {points} امتیازات اضافه شول.",
        "en": "🎁 Congrats! Your daily {points} points have been added.",
    },
    "daily_bonus_wait": {
        "fa": "⏳ شما قبلاً جایزه امروز را گرفته‌اید. فردا دوباره تلاش کنید.",
        "ps": "⏳ تاسو نننۍ بونس مخکې اخیستی. سبا بیا هڅه وکړئ.",
        "en": "⏳ You've already claimed today's bonus. Try again tomorrow.",
    },

    "no_tasks": {
        "fa": "در حال حاضر وظیفه‌ای موجود نیست.",
        "ps": "اوس مهال هېڅ ټاسک نشته.",
        "en": "No tasks available right now.",
    },
    "task_join_prompt": {
        "fa": "📺 عضو کانال زیر شوید سپس روی «بررسی» کلیک کنید:\n{channel}",
        "ps": "📺 لاندې چینل ته جوائن شئ او بیا «چک کول» کیکل کړئ:\n{channel}",
        "en": "📺 Join this channel then tap 'Verify':\n{channel}",
    },
    "verify_btn": {"fa": "✅ بررسی عضویت", "ps": "✅ د غړیتوب چک", "en": "✅ Verify Membership"},
    "task_success": {
        "fa": "✅ عالی! {points} امتیاز دریافت کردید.",
        "ps": "✅ ښه! تاسو ته {points} امتیازات ورکړل شول.",
        "en": "✅ Great! You earned {points} points.",
    },
    "task_not_joined": {
        "fa": "❌ شما هنوز عضو کانال نشده‌اید. لطفاً ابتدا عضو شوید.",
        "ps": "❌ تاسو تر اوسه چینل ته جوائن شوي نه یاست. لومړی جوائن شئ.",
        "en": "❌ You haven't joined the channel yet. Please join first.",
    },
    "task_already_done": {
        "fa": "ℹ️ شما قبلاً این وظیفه را انجام داده‌اید.",
        "ps": "ℹ️ تاسو دا ټاسک مخکې ترسره کړی دی.",
        "en": "ℹ️ You've already completed this task.",
    },

    "referral_msg": {
        "fa": "👥 لینک دعوت شما:\n{link}\n\nبه ازای هر دوست: {points} امتیاز\nتعداد افراد دعوت شده: {count}",
        "ps": "👥 ستاسو د بلنې لینک:\n{link}\n\nپه هر ملګري: {points} امتیازات\nبللي کسان: {count}",
        "en": "👥 Your referral link:\n{link}\n\nPer friend: {points} points\nInvited so far: {count}",
    },

    "withdraw_ask_amount": {
        "fa": "💵 چند امتیاز می‌خواهید برداشت کنید؟\n(حداقل: {min_points} امتیاز = {min_usdt} USDT)",
        "ps": "💵 څو امتیازات غواړئ ووباسئ؟\n(لږترلږه: {min_points} امتیازات = {min_usdt} USDT)",
        "en": "💵 How many points do you want to withdraw?\n(Minimum: {min_points} points = {min_usdt} USDT)",
    },
    "withdraw_ask_address": {
        "fa": "🔑 آدرس والت USDT (شبکه TRC20) خود را ارسال کنید:",
        "ps": "🔑 خپل USDT والټ ایډریس (د TRC20 شبکه) ولیږئ:",
        "en": "🔑 Send your USDT wallet address (TRC20 network):",
    },
    "withdraw_too_low": {
        "fa": "❌ موجودی کافی نیست یا مبلغ کمتر از حداقل مجاز است.",
        "ps": "❌ بیلانس بس نه دی یا اندازه له لږترلږه حد نه کمه ده.",
        "en": "❌ Insufficient balance or below the minimum withdrawal amount.",
    },
    "withdraw_submitted": {
        "fa": "✅ درخواست برداشت شما ثبت شد و در انتظار تایید ادمین است.\nشناسه درخواست: #{req_id}",
        "ps": "✅ ستاسو د وتلو غوښتنه ثبت شوه او د ادمین تایید ته انتظار باسي.\nد غوښتنې شمېره: #{req_id}",
        "en": "✅ Your withdrawal request has been submitted and is pending admin approval.\nRequest ID: #{req_id}",
    },
    "invalid_number": {
        "fa": "❌ لطفاً یک عدد معتبر ارسال کنید.",
        "ps": "❌ مهرباني وکړئ سم عدد ولیږئ.",
        "en": "❌ Please send a valid number.",
    },

    "admin_new_withdraw": {
        "fa": "🔔 درخواست برداشت جدید\nکاربر: {user_id}\nمبلغ: {usdt} USDT ({points} امتیاز)\nآدرس: {address}\nشناسه: #{req_id}",
        "ps": "🔔 نوې د وتلو غوښتنه\nکاروونکی: {user_id}\nاندازه: {usdt} USDT ({points} امتیازات)\nایډریس: {address}\nشمېره: #{req_id}",
        "en": "🔔 New withdrawal request\nUser: {user_id}\nAmount: {usdt} USDT ({points} points)\nAddress: {address}\nRequest: #{req_id}",
    },
    "withdraw_approved_user": {
        "fa": "✅ درخواست برداشت شما (#{req_id}) تایید و پرداخت شد.",
        "ps": "✅ ستاسو د وتلو غوښتنه (#{req_id}) تایید او ورکړل شوه.",
        "en": "✅ Your withdrawal request (#{req_id}) was approved and paid.",
    },
    "withdraw_rejected_user": {
        "fa": "❌ درخواست برداشت شما (#{req_id}) رد شد و امتیاز به حساب شما برگشت.",
        "ps": "❌ ستاسو د وتلو غوښتنه (#{req_id}) رد شوه او امتیازات مو بیرته بیلانس ته ولاړل.",
        "en": "❌ Your withdrawal request (#{req_id}) was rejected and points were refunded.",
    },

    "cancel_btn": {"fa": "لغو", "ps": "لغوه کول", "en": "Cancel"},
    "cancelled": {"fa": "لغو شد.", "ps": "لغوه شو.", "en": "Cancelled."},
    "back_btn": {"fa": "🔙 بازگشت", "ps": "🔙 شاته", "en": "🔙 Back"},
}


def t(key: str, lang: str, **kwargs) -> str:
    """Get translated text for a key and language, formatted with kwargs."""
    lang = lang if lang in ("fa", "ps", "en") else "en"
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", key))
    if kwargs:
        return text.format(**kwargs)
    return text
