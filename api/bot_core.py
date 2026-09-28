import telebot
import os
import json
import random
import string
import psutil
from datetime import datetime, timedelta
from telebot import types

# ==================== AYARLAR ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8966507928:AAGooka4e_eRlTixOF0xZulAsTh8Wi1N8go").strip()
BOT_USERNAME = "logsuzlarhostbot"
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8727961464))
ADMIN_USERNAME = "izeyder"
KURUCU = "izeyder"
CHANNEL_USERNAME = "logsuzlarpanel"

FREE_LIMIT = 2
PRIME_LIMIT = 5
DATA_DIR = "/tmp/hosting_data"
os.makedirs(DATA_DIR, exist_ok=True)

HOSTED_FILE = f"{DATA_DIR}/hosted_bots.json"
USERS_FILE = f"{DATA_DIR}/users.json"
CODES_FILE = f"{DATA_DIR}/prime_codes.json"

PRIME_PRICE_30_DAYS = "İletişime Geç"

# ==================== PREMIUM EMOJİLER ====================
E_GIF_ID = "5287641556453438598"
E_ROCKET_ID = "6030488126328150178"
E_CROWN_ID = "5904286619778685390"
E_GEM_ID = "5904586614654376665"
E_STAR_ID = "6028219653451421613"
E_CHECK_ID = "6030329839603422901"
E_CROSS_ID = "6030581340003375192"
E_LOCK_ID = "6035240365907254232"
E_BELL_ID = "6030824151684487229"
E_FIRE_ID = "6030661071776257635"
E_HEART_ID = "5904667557608037036"
E_HOME_ID = "6035130268715588895"
E_SPARK_ID = "6030448939046541756"
E_INFO_ID = "6035156545325506346"

def E(eid, char):
    return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'

E_GIF = E(E_GIF_ID, "🎬")
E_ROCKET = E(E_ROCKET_ID, "🚀")
E_CROWN = E(E_CROWN_ID, "👑")
E_GEM = E(E_GEM_ID, "💎")
E_STAR = E(E_STAR_ID, "⭐")
E_CHECK = E(E_CHECK_ID, "✅")
E_CROSS = E(E_CROSS_ID, "❌")
E_LOCK = E(E_LOCK_ID, "🔒")
E_BELL = E(E_BELL_ID, "🔔")
E_FIRE = E(E_FIRE_ID, "🔥")
E_HEART = E(E_HEART_ID, "❤️")
E_HOME = E(E_HOME_ID, "🏠")
E_SPARK = E(E_SPARK_ID, "✨")
E_INFO = E(E_INFO_ID, "ℹ️")

PM = "HTML"

# ==================== JSON DB ====================
def _load(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return default

def _save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def load_users(): return _load(USERS_FILE, {})
def save_users(d): _save(USERS_FILE, d)
def load_bots(): return _load(HOSTED_FILE, {})
def save_bots(d): _save(HOSTED_FILE, d)
def load_codes(): return _load(CODES_FILE, {})
def save_codes(d): _save(CODES_FILE, d)

# ==================== YARDIMCI ====================
def register_user(user_id, ref_by=None):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "is_prime": 0,
            "prime_expire": None,
            "referred_by": ref_by,
            "referral_count": 0,
            "first_seen": datetime.now().isoformat()
        }
        if ref_by and str(ref_by) != uid:
            ref_key = str(ref_by)
            if ref_key in users:
                users[ref_key]["referral_count"] = users[ref_key].get("referral_count", 0) + 1
                if users[ref_key]["referral_count"] % 3 == 0:
                    add_prime_days(ref_by, 1)
        save_users(users)
        return True
    return False

def is_prime_user(user_id):
    if user_id == ADMIN_ID: return True
    users = load_users()
    u = users.get(str(user_id), {})
    if u.get("is_prime") == 1:
        exp = u.get("prime_expire")
        if exp:
            try:
                if datetime.now() > datetime.fromisoformat(exp):
                    u["is_prime"] = 0
                    u["prime_expire"] = None
                    save_users(users)
                    return False
            except: pass
        return True
    return False

def add_prime_days(user_id, days):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"is_prime": 0, "prime_expire": None, "referred_by": None, "referral_count": 0}
    now = datetime.now()
    cur = users[uid].get("prime_expire")
    if cur:
        try:
            ce = datetime.fromisoformat(cur)
            ne = (ce if ce > now else now) + timedelta(days=days)
        except: ne = now + timedelta(days=days)
    else: ne = now + timedelta(days=days)
    users[uid]["is_prime"] = 1
    users[uid]["prime_expire"] = ne.isoformat()
    save_users(users)

def safe_send(bot, chat_id, text, markup=None):
    try:
        return bot.send_message(chat_id, text, parse_mode=PM, reply_markup=markup)
    except:
        import re
        cleaned = re.sub(r'<tg-emoji emoji-id="[^"]+">([^<]+)</tg-emoji>', r'\1', text)
        try:
            return bot.send_message(chat_id, cleaned, parse_mode=PM, reply_markup=markup)
        except:
            try:
                return bot.send_message(chat_id, re.sub(r'<[^>]+>', '', text), reply_markup=markup)
            except: return None

def safe_edit(bot, chat_id, msg_id, text, markup=None):
    try:
        bot.edit_message_text(text, chat_id, msg_id, parse_mode=PM, reply_markup=markup)
    except Exception as e:
        if "not modified" in str(e).lower(): return
        safe_send(bot, chat_id, text, markup)

# ==================== MENÜLER ====================
def ana_menu(user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("📤 Bot Yükle (.py)", callback_data="upload_info"),
        types.InlineKeyboardButton("📱 Botlarım", callback_data="my_bots")
    )
    m.add(types.InlineKeyboardButton("💎 PRIME VIP BÖLGE 🌟", callback_data="prime_zone"))
    m.add(
        types.InlineKeyboardButton("👥 Referans Sistemi", callback_data="referral_info"),
        types.InlineKeyboardButton("🎟️ Kupon Kullan", callback_data="claim_code")
    )
    m.add(
        types.InlineKeyboardButton("📊 Sunucu Durumu", callback_data="server_stats"),
        types.InlineKeyboardButton("❓ Yardım", callback_data="help_guide")
    )
    m.add(
        types.InlineKeyboardButton("📢 Resmi Kanal", url=f"https://t.me/{CHANNEL_USERNAME}"),
        types.InlineKeyboardButton("📞 Admin", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    if user_id == ADMIN_ID:
        m.add(types.InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel"))
    m.add(types.InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu"))
    return m

def prime_klavye():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💳 Ödeme Bilgisi", callback_data="pay_info"),
        types.InlineKeyboardButton("⏳ Abonelik Durumu", callback_data="prime_expire_check")
    )
    m.add(
        types.InlineKeyboardButton("🎁 Arkadaşa Hediye", callback_data="gift_prime"),
        types.InlineKeyboardButton("🎟️ Kupon Kullan", callback_data="claim_code")
    )
    m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
    return m

# ==================== BOT OLUŞTUR ====================
def create_bot(token):
    bot = telebot.TeleBot(token, threaded=False, parse_mode=None)

    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        ref_by = None
        args = message.text.split()
        if len(args) > 1 and args[1].startswith("ref_"):
            try: ref_by = int(args[1].replace("ref_", ""))
            except: pass

        register_user(user_id, ref_by)
        is_p = is_prime_user(user_id)
        name = message.from_user.first_name or "Kullanıcı"
        badge = f"{E_CROWN} PRIME VIP ÜYE" if is_p else "🆓 STANDART ÜYE"
        limit_info = f"🚀 Hosting Limiti: <b>{PRIME_LIMIT}</b> Bot" if is_p else f"📦 Hosting Limiti: <b>{FREE_LIMIT}</b> Bot"

        msg = (
            f"{E_GIF} <b>LOGSUZLAR HOSTING</b> {E_GIF}\n"
            f"{E_ROCKET} <b>Server v3.0</b> {E_ROCKET}\n\n"
            f"✨ <b>Hoş geldin, {name}!</b>\n\n"
            f"👤 <b>Profil Kartı:</b>\n"
            f" ├ 🏷️ <b>İsim:</b> <code>{name}</code>\n"
            f" ├ 🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f" └ 💎 <b>Durum:</b> <b>{badge}</b>\n\n"
            f"⚡ <b>Hizmetler:</b>\n"
            f" ├ {limit_info}\n"
            f" └ 🛡️ <b>Crash Guard:</b> {'24/7 Aktif' if is_p else 'Sadece Prime'}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 <b>Seçenekler:</b>"
        )
        safe_send(bot, message.chat.id, msg, ana_menu(user_id))

    @bot.message_handler(commands=['approve'])
    def approve_cmd(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split(maxsplit=2)
            target_uid = int(parts[1]); fname = parts[2]
            bots = load_bots()
            key = f"{target_uid}_{fname}"
            if key in bots:
                bots[key]["approved"] = 1
                save_bots(bots)
                try: safe_send(bot, target_uid, f"{E_CHECK} <b>Botun onaylandı!</b>\n📄 <code>{fname}</code>")
                except: pass
                bot.reply_to(message, f"{E_CHECK} Onaylandı.")
            else: bot.reply_to(message, f"{E_CROSS} Bulunamadı.")
        except: bot.reply_to(message, "Kullanım: /approve USER_ID FILE.py")

    @bot.message_handler(commands=['reject'])
    def reject_cmd(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split(maxsplit=2)
            target_uid = int(parts[1]); fname = parts[2]
            bots = load_bots()
            key = f"{target_uid}_{fname}"
            if key in bots:
                del bots[key]
                save_bots(bots)
                try: safe_send(bot, target_uid, f"{E_CROSS} Botun reddedildi.")
                except: pass
                bot.reply_to(message, f"{E_CROSS} Reddedildi.")
            else: bot.reply_to(message, f"{E_CROSS} Bulunamadı.")
        except: bot.reply_to(message, "Kullanım: /reject USER_ID FILE.py")

    @bot.message_handler(commands=['genkey'])
    def gen_key(message):
        if message.from_user.id != ADMIN_ID: return
        try: days = int(message.text.split()[1])
        except: days = 30
        code = "PRIME-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        codes = load_codes()
        codes[code] = days
        save_codes(codes)
        bot.reply_to(message, f"🎟️ <b>Prime Kod:</b>\n<code>{code}</code> ({days} Gün)", parse_mode=PM)

    @bot.message_handler(commands=['pending'])
    def pending_cmd(message):
        if message.from_user.id != ADMIN_ID: return
        bots = load_bots()
        pend = [k for k, v in bots.items() if not v.get("approved")]
        if not pend:
            bot.reply_to(message, f"{E_CHECK} Bekleyen yok."); return
        txt = f"{E_BELL} <b>BEKLEYEN ONAYLAR</b>\n\n"
        for k in pend:
            uid, fn = k.split("_", 1)
            txt += f"👤 <code>{uid}</code> · 📄 <code>{fn}</code>\n"
        bot.reply_to(message, txt, parse_mode=PM)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        try: bot.answer_callback_query(call.id)
        except: pass

        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        d = call.data

        if d == "main_menu":
            safe_edit(bot, chat_id, msg_id, "🏠 <b>Ana Menü:</b>", ana_menu(user_id))

        elif d == "prime_zone":
            st = f"{E_CROWN} PRIME VIP ÜYE" if is_prime_user(user_id) else "🆓 STANDART ÜYE"
            msg = (
                f"{E_CROWN} <b>PRIME VIP BÖLGE</b> {E_CROWN}\n"
                f"{E_GIF} <i>Logsuzlar Hosting</i>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Durumun:</b> {st}\n\n"
                f"{E_FIRE} <b>Prime Özellikleri:</b>\n"
                f" ├ 🚀 <b>{PRIME_LIMIT}</b> Bot Hosting\n"
                f" ├ ⚡ Yüksek Öncelik\n"
                f" ├ 🛡️ Otomatik Crash Guard\n"
                f" └ 🎧 VIP Destek\n\n"
                f"💰 <b>Fiyat:</b> {PRIME_PRICE_30_DAYS} / 30 Gün"
            )
            safe_edit(bot, chat_id, msg_id, msg, prime_klavye())

        elif d == "pay_info":
            msg = (
                f"💳 <b>Ödeme Bilgisi</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"Admin ile iletişime geç:\n\n"
                f"📞 <b>Admin:</b> @{ADMIN_USERNAME}\n"
                f"👑 <b>Kurucu:</b> @{KURUCU}\n"
                f"💰 <b>Fiyat:</b> {PRIME_PRICE_30_DAYS}"
            )
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("💬 Admine Yaz", url=f"https://t.me/{ADMIN_USERNAME}"))
            m.add(types.InlineKeyboardButton("🔙 Prime Bölge", callback_data="prime_zone"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "prime_expire_check":
            users = load_users()
            u = users.get(str(user_id), {})
            if is_prime_user(user_id):
                exp = u.get("prime_expire") or "Sınırsız (Admin)"
                msg = f"{E_STAR} <b>Prime VIP Aktif!</b>\n⏳ <b>Bitiş:</b> <code>{exp}</code>"
            else:
                msg = f"{E_CROSS} <b>Aktif Prime VIP aboneliğin yok.</b>"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Prime Bölge", callback_data="prime_zone"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "gift_prime":
            if not is_prime_user(user_id):
                safe_edit(bot, chat_id, msg_id, f"{E_CROSS} Sadece Prime üyeler hediye edebilir!"); return
            m = bot.send_message(chat_id, "🎁 <b>Hedef kullanıcının ID'sini gir:</b>", parse_mode=PM)
            bot.register_next_step_handler(m, process_gift)

        elif d == "upload_info":
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id,
                f"📥 <b>Python dosyanı (.py) direkt bu sohbete gönder.</b>\n\n"
                f"{E_LOCK} Admin onayı sonrası görünür.",
                m)

        elif d == "referral_info":
            users = load_users()
            ref = users.get(str(user_id), {}).get("referral_count", 0)
            link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
            msg = (
                f"👥 <b>Referans Sistemi</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 <b>Linkin:</b>\n<code>{link}</code>\n\n"
                f"📊 <b>Referansların:</b> <code>{ref}</code>\n"
                f"🎁 <b>Ödül:</b> Her 3 davet = 1 gün Prime VIP"
            )
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "server_stats":
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            bots = load_bots()
            total = len(bots)
            run = len([k for k, v in bots.items() if v.get("approved")])
            pend = total - run

            cpu_bar = "█" * int(cpu / 10) + "░" * (10 - int(cpu / 10))
            ram_bar = "█" * int(ram.percent / 10) + "░" * (10 - int(ram.percent / 10))

            msg = (
                f"🖥️ <b>Sunucu Anlık Durum</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 <b>CPU:</b> <code>{cpu:.1f}%</code> {cpu_bar}\n"
                f"💾 <b>RAM:</b> <code>{ram.percent:.1f}%</code> {ram_bar}\n"
                f"📦 <b>Toplam:</b> <code>{ram.total // (1024**3)} GB</code>\n"
                f"⚙️ <b>CPU Çekirdek:</b> <code>{psutil.cpu_count()}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 <b>Toplam Bot:</b> <code>{total}</code>\n"
                f"✅ <b>Onaylı:</b> <code>{run}</code>\n"
                f"⏳ <b>Bekleyen:</b> <code>{pend}</code>"
            )
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔄 Yenile", callback_data="server_stats"))
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "help_guide":
            msg = (
                f"❓ <b>Yardım</b>\n\n"
                f"1️⃣ <code>.py</code> dosyanı yükle\n"
                f"2️⃣ <b>Botlarım</b>'a git\n"
                f"3️⃣ {E_LOCK} Admin onayını bekle\n"
                f"4️⃣ Onay sonrası admin çalıştırır\n\n"
                f"⚠️ Vercel serverless olduğu için bot çalıştırma sınırlıdır."
            )
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "claim_code":
            m = bot.send_message(chat_id, "🎟️ <b>Kupon kodunu gir:</b>", parse_mode=PM)
            bot.register_next_step_handler(m, process_claim)

        elif d == "admin_panel":
            if user_id != ADMIN_ID: return
            users = load_users()
            bots = load_bots()
            u = len(users)
            p = len([x for x in users.values() if x.get("is_prime")])
            b = len(bots)
            pend = len([k for k, v in bots.items() if not v.get("approved")])

            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent

            msg = (
                f"{E_CROWN} <b>ADMİN PANEL</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 CPU: <code>{cpu:.1f}%</code> · 💾 RAM: <code>{ram:.1f}%</code>\n\n"
                f"👥 Kullanıcı: <code>{u}</code>\n"
                f"{E_GEM} Prime: <code>{p}</code>\n"
                f"🤖 Toplam Bot: <code>{b}</code>\n"
                f"⏳ Onay Bekleyen: <code>{pend}</code>\n\n"
                f"Komutlar:\n"
                f"<code>/approve USER_ID FILE</code>\n"
                f"<code>/reject USER_ID FILE</code>\n"
                f"<code>/genkey DAYS</code>\n"
                f"<code>/pending</code>"
            )
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("⏳ Bekleyenler", callback_data="list_pending"))
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d == "list_pending":
            if user_id != ADMIN_ID: return
            bots = load_bots()
            pend = [k for k, v in bots.items() if not v.get("approved")]
            if not pend:
                safe_edit(bot, chat_id, msg_id, f"{E_CHECK} Bekleyen yok."); return
            txt = f"{E_BELL} <b>BEKLEYEN ONAYLAR</b>\n\n"
            for k in pend:
                uid, fn = k.split("_", 1)
                txt += f"👤 <code>{uid}</code> · 📄 <code>{fn}</code>\n"
                txt += f"<code>/approve {uid} {fn}</code>\n\n"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel"))
            safe_edit(bot, chat_id, msg_id, txt, m)

        elif d == "my_bots":
            bots = load_bots()
            user_bots = {k: v for k, v in bots.items() if k.startswith(f"{user_id}_")}
            if not user_bots:
                m = types.InlineKeyboardMarkup()
                m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
                safe_edit(bot, chat_id, msg_id, f"{E_CROSS} Yüklü botun yok.", m); return
            m = types.InlineKeyboardMarkup()
            for k, v in user_bots.items():
                fn = k.split("_", 1)[1]
                icon = "✅" if v.get("approved") else "⏳"
                m.add(types.InlineKeyboardButton(f"{icon} {fn}", callback_data=f"manage_{k}"))
            m.add(types.InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu"))
            safe_edit(bot, chat_id, msg_id, "⚙️ <b>Yönetmek için bot seç:</b>", m)

        elif d.startswith("manage_"):
            key = d[7:]
            bots = load_bots()
            b = bots.get(key)
            if not b:
                safe_edit(bot, chat_id, msg_id, f"{E_CROSS} Bulunamadı."); return
            uid_key = key.split("_", 1)[0]
            if int(uid_key) != user_id and user_id != ADMIN_ID:
                safe_edit(bot, chat_id, msg_id, f"{E_CROSS} Yetkin yok."); return

            fn = key.split("_", 1)[1]
            status = "✅ Onaylı" if b.get("approved") else "⏳ Onay Bekliyor"

            msg = (
                f"🤖 <b>Bot Kontrol Paneli</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📄 <b>Dosya:</b> <code>{fn}</code>\n"
                f"📊 <b>Durum:</b> {status}\n"
                f"📅 <b>Yükleme:</b> <code>{b.get('uploaded', 'N/A')[:19]}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <i>Vercel serverless modunda child process çalıştırılamaz.</i>"
            )
            m = types.InlineKeyboardMarkup(row_width=2)
            if not b.get("approved") and user_id == ADMIN_ID:
                m.add(
                    types.InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{key}"),
                    types.InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{key}")
                )
            m.add(types.InlineKeyboardButton("🗑️ Botu Sil", callback_data=f"delbot_{key}"))
            m.add(types.InlineKeyboardButton("🔙 Botlarım", callback_data="my_bots"))
            safe_edit(bot, chat_id, msg_id, msg, m)

        elif d.startswith("approve_"):
            if user_id != ADMIN_ID: return
            key = d[8:]
            bots = load_bots()
            if key in bots:
                bots[key]["approved"] = 1
                save_bots(bots)
                uid = int(key.split("_", 1)[0])
                fn = key.split("_", 1)[1]
                try: safe_send(bot, uid, f"{E_CHECK} <b>Botun onaylandı!</b>\n📄 <code>{fn}</code>")
                except: pass
                safe_edit(bot, chat_id, msg_id, f"{E_CHECK} Onaylandı.", None)

        elif d.startswith("reject_"):
            if user_id != ADMIN_ID: return
            key = d[7:]
            bots = load_bots()
            if key in bots:
                uid = int(key.split("_", 1)[0])
                fn = key.split("_", 1)[1]
                del bots[key]
                save_bots(bots)
                try: safe_send(bot, uid, f"{E_CROSS} Botun reddedildi.")
                except: pass
                safe_edit(bot, chat_id, msg_id, f"{E_CROSS} Reddedildi.", None)

        elif d.startswith("delbot_"):
            key = d[7:]
            bots = load_bots()
            b = bots.get(key)
            if not b: return
            uid_key = int(key.split("_", 1)[0])
            if uid_key != user_id and user_id != ADMIN_ID: return
            del bots[key]
            save_bots(bots)
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("🔙 Botlarım", callback_data="my_bots"))
            safe_edit(bot, chat_id, msg_id, f"{E_CHECK} Bot silindi.", m)

    @bot.message_handler(content_types=['document'])
    def handle_document(message):
        user_id = message.from_user.id
        register_user(user_id)

        if not message.document.file_name or not message.document.file_name.endswith('.py'):
            bot.reply_to(message, f"{E_CROSS} <b>Geçersiz format!</b> Sadece <code>.py</code> dosyası yükleyin.", parse_mode=PM)
            return

        is_p = is_prime_user(user_id)
        max_allowed = PRIME_LIMIT if is_p else FREE_LIMIT
        filename = message.document.file_name

        bots = load_bots()
        user_bots = {k: v for k, v in bots.items() if k.startswith(f"{user_id}_")}

        if f"{user_id}_{filename}" not in bots and len(user_bots) >= max_allowed:
            bot.reply_to(message,
                f"⚠️ <b>Limit Doldu!</b>\n\n"
                f"{E_INFO} Maksimum <b>{max_allowed}</b> bot yükleyebilirsin.",
                parse_mode=PM)
            return

        info = bot.get_file(message.document.file_id)
        dl = bot.download_file(info.file_path)

        user_dir = os.path.join(DATA_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, filename)

        with open(filepath, 'wb') as f: f.write(dl)

        key = f"{user_id}_{filename}"
        bots[key] = {
            "user_id": user_id,
            "filename": filename,
            "filepath": filepath,
            "approved": 0,
            "uploaded": datetime.now().isoformat()
        }
        save_bots(bots)

        try:
            safe_send(bot, ADMIN_ID,
                f"{E_BELL} <b>YENİ BOT YÜKLEMESİ</b>\n\n"
                f"👤 Kullanıcı: <code>{user_id}</code>\n"
                f"📄 Dosya: <code>{filename}</code>\n\n"
                f"Onayla: <code>/approve {user_id} {filename}</code>\n"
                f"Reddet: <code>/reject {user_id} {filename}</code>")
        except: pass

        bot.reply_to(message,
            f"{E_CHECK} <b>{filename}</b> yüklendi!\n\n"
            f"{E_LOCK} <b>Admin onayı bekleniyor...</b>",
            parse_mode=PM)

    def process_claim(message):
        if not message.text:
            bot.reply_to(message, f"{E_CROSS} Geçersiz."); return
        code = message.text.strip()
        codes = load_codes()
        if code in codes:
            days = codes[code]
            add_prime_days(message.from_user.id, days)
            del codes[code]
            save_codes(codes)
            bot.reply_to(message, f"{E_CHECK} <b>{days} gün Prime VIP aktif!</b>", parse_mode=PM)
        else:
            bot.reply_to(message, f"{E_CROSS} <b>Geçersiz kod!</b>", parse_mode=PM)

    def process_gift(message):
        if not message.text or not message.text.isdigit():
            bot.reply_to(message, f"{E_CROSS} Geçersiz ID."); return
        try:
            fid = int(message.text.strip())
            add_prime_days(fid, 7)
            bot.reply_to(message, f"{E_CHECK} <code>{fid}</code> kullanıcısına 7 gün Prime hediye edildi!", parse_mode=PM)
            try:
                safe_send(bot, fid, f"{E_GEM} <b>HEDİYE PRIME VIP!</b>\n\n7 gün Prime hediye aldın!")
            except: pass
        except: bot.reply_to(message, f"{E_CROSS} Hata.")

    return bot
