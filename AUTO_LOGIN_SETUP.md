# Auto-Login Setup Guide

## Overview

Sistem sekarang mendukung **auto-login** untuk TikTok, Instagram, dan Facebook untuk:
- ✅ **Avoid CAPTCHA** (sudah login = less likely trigger anti-bot)
- ✅ **No login popups** (langsung akses content)
- ✅ **Higher rate limits** (sebagai authenticated user)
- ✅ **Access private content** (jika akun Anda punya akses)

---

## Setup Credentials

### 1. Edit `.env` File

Buka file: `d:\.dev\python\crawling\.env`

Isi credentials:

```bash
# Social Media Login Credentials (Auto-login to avoid CAPTCHA)
# TikTok
TIKTOK_USERNAME=your_tiktok_username
TIKTOK_PASSWORD=your_tiktok_password

# Instagram
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# Facebook
FACEBOOK_EMAIL=your_facebook_email@example.com
FACEBOOK_PASSWORD=your_facebook_password
```

**IMPORTANT:**
- Use **dedicated crawler accounts** (bukan akun personal utama!)
- Credentials di-save **local** di `.env` - jangan commit ke Git
- Pastikan `.env` ada di `.gitignore`

---

## How It Works

### TikTok Auto-Login

**File**: `crawler-worker/crawlers/tiktok_crawler.py`

**Flow:**
1. Initialize browser
2. **Navigate to TikTok login page**
3. **Fill username & password**
4. **Click login button**
5. **Wait for redirect** to homepage
6. Navigate to target video
7. Crawl comments (no popup, no CAPTCHA!)

**Logs:**
```
INFO: Attempting TikTok login for user: your_username
INFO: Login button clicked, waiting for redirect...
INFO: ✅ TikTok login successful!
INFO: Starting TikTok crawl for https://...
```

---

### Instagram Auto-Login

**File**: `crawler-worker/crawlers/instagram_crawler.py`

**Flow:**
1. Initialize browser
2. **Navigate to Instagram login**
3. **Fill credentials**
4. **Handle "Save Login Info" popup** (click "Not Now")
5. **Handle "Turn on Notifications" popup** (click "Not Now")
6. Navigate to target post
7. Crawl comments (no login popup!)

**Logs:**
```
INFO: Attempting Instagram login for user: your_username
INFO: ✅ Instagram login successful!
INFO: Starting Instagram crawl for https://...
```

---

### Facebook Auto-Login

**File**: `crawler-worker/crawlers/facebook_crawler.py`

**Flow:**
1. Initialize browser
2. **Navigate to Facebook login**
3. **Fill email & password**
4. **Click login**
5. Navigate to target post
6. Crawl comments

---

## Testing Auto-Login

### 1. Set Credentials

Edit `.env`:
```bash
TIKTOK_USERNAME=testaccount123
TIKTOK_PASSWORD=YourPassword123!
```

### 2. Run with `headless=False` (untuk lihat browser)

Edit `crawler-worker/main.py` line 91:
```python
crawler = TikTokCrawler(headless=False)  # See login process
```

### 3. Restart Worker

```bash
cd D:\.dev\python\crawling\crawler-worker
python main.py
```

### 4. Submit Job via Postman

**Browser akan muncul** dan Anda bisa lihat:
1. Login page
2. Auto-fill username/password
3. Login button click
4. Redirect to homepage
5. Navigate to video
6. Crawl comments

**No CAPTCHA, no popup!** ✅

---

## Troubleshooting

### Login Gagal / Still Shows CAPTCHA

**Possible causes:**
1. **2FA enabled** - Disable 2FA untuk crawler account
2. **Suspicious activity** - Akun terlalu baru atau belum verified
3. **Wrong credentials** - Check typo di `.env`
4. **IP banned** - Terlalu banyak login attempts

**Solutions:**
- Use **aged accounts** (>6 months old, ada activity)
- **Verify email/phone** untuk akun crawler
- **Disable 2FA** di security settings
- **Login manual** 1x dari browser biasa di IP yang sama

### Login Timeout

**Fix:** Increase timeout di code:
```python
self.page.goto('...', timeout=60000)  # 60s
```

### "Not Now" Button Not Found

Instagram kadang tidak show popup - ini normal, crawler skip dan lanjut.

---

## Security Best Practices

### ✅ DO:
- Use **dedicated crawler accounts**
- Keep `.env` file **LOCAL ONLY**
- Add `.env` to `.gitignore`
- Use **strong, unique passwords**
- Monitor account activity

### ❌ DON'T:
- Don't use **personal accounts** (risk banned!)
- Don't commit `.env` to Git
- Don't share credentials
- Don't enable 2FA (prevents auto-login)
- Don't login terlalu sering (1-2x per day OK)

---

## Production Deployment

### Option 1: Environment Variables

Instead of `.env` file:
```bash
export TIKTOK_USERNAME=your_username
export TIKTOK_PASSWORD=your_password
```

### Option 2: Secret Manager

AWS Secrets Manager, Azure Key Vault, etc.

```python
import boto3

secrets = boto3.client('secretsmanager')
credentials = secrets.get_secret_value(SecretId='social-crawler-creds')
```

### Option 3: No Auto-Login (Use Cookies)

Export cookies dari logged-in session, load di crawler:
```python
with open('cookies.json', 'r') as f:
    cookies = json.load(f)
    browser_context.add_cookies(cookies)
```

**Benefit**: No need credentials, more secure.

---

## Rate Limiting Recommendation

Bahkan dengan auto-login, jangan crawl terlalu agresif:

**Recommended limits:**
- **TikTok**: 1 video per 5 minutes (~12/hour, ~288/day)
- **Instagram**: 1 post per 3 minutes (~20/hour, ~480/day)
- **Facebook**: 1 post per 5 minutes (~12/hour)

**Jika lebih dari itu**: Use multiple accounts + rotating proxies.

---

## Files Modified

1. [`.env`](file:///d:/.dev/python/crawling/.env) - Added credentials section
2. [`tiktok_crawler.py`](file:///d:/.dev/python/crawling/crawler-worker/crawlers/tiktok_crawler.py) - Added `_login_tiktok()`
3. [`instagram_crawler.py`](file:///d:/.dev/python/crawling/crawler-worker/crawlers/instagram_crawler.py) - Added `_login_instagram()`
4. [`facebook_crawler.py`](file:///d:/.dev/python/crawling/crawler-worker/crawlers/facebook_crawler.py) - Added `_login_facebook()` (TODO)

---

## Next Steps

1. **Create dedicated crawler accounts** untuk TikTok & Instagram
2. **Disable 2FA** di account settings
3. **Verify email/phone** jika belum
4. **Add credentials** ke `.env`
5. **Test** dengan `headless=False` untuk lihat login process
6. **Monitor logs** untuk confirm login successful
7. **Switch back** to `headless=True` untuk production

Selamat crawling without CAPTCHA! 🚀
