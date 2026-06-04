#!/usr/bin/env python3
"""
Git Backdate Tool
Buat commit dengan tanggal custom agar GitHub contribution graph menyala hijau.
"""

import subprocess
import sys
import os
from datetime import datetime

# ──────────────────────────────────────────
# ANSI Colors
# ──────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def cprint(color, text):
    print(f"{color}{text}{RESET}")

def header():
    print()
    cprint(BOLD + CYAN, "╔══════════════════════════════════════════╗")
    cprint(BOLD + CYAN, "║        🟩  Git Backdate Tool  🟩          ║")
    cprint(BOLD + CYAN, "║   Buat commit mundur — GitHub go green   ║")
    cprint(BOLD + CYAN, "╚══════════════════════════════════════════╝")
    print()

def check_git_repo():
    """Pastikan kita berada di dalam git repo."""
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        cprint(RED, "❌ Folder ini bukan git repository!")
        cprint(YELLOW, "   Jalankan: git init  lalu coba lagi.")
        sys.exit(1)
    cprint(GREEN, "✅ Git repository terdeteksi.")

def check_remote():
    """Cek apakah remote (GitHub) sudah terhubung."""
    result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
    if not result.stdout.strip():
        cprint(YELLOW, "⚠️  Belum ada remote GitHub terhubung.")
        cprint(YELLOW, "   Tambahkan dulu: git remote add origin <URL_REPO>")
        add = input("   Masukkan URL repo GitHub (kosongkan untuk skip): ").strip()
        if add:
            subprocess.run(["git", "remote", "add", "origin", add])
            cprint(GREEN, "✅ Remote ditambahkan.")
    else:
        cprint(GREEN, "✅ Remote GitHub terhubung:")
        for line in result.stdout.strip().split("\n"):
            print(f"   {line}")

def parse_date(date_str):
    """Parse input tanggal dari berbagai format."""
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d %m %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def parse_time(time_str):
    """Parse input waktu HH:MM."""
    try:
        return datetime.strptime(time_str.strip(), "%H:%M")
    except ValueError:
        return None

def get_date_input():
    """Minta input tanggal dari user."""
    cprint(CYAN, "\n📅 Masukkan tanggal commit:")
    cprint(YELLOW, "   Format: YYYY-MM-DD  atau  DD-MM-YYYY  atau  DD/MM/YYYY")
    cprint(YELLOW, "   Contoh: 2024-03-15  atau  15-03-2024")
    while True:
        date_str = input("   Tanggal: ").strip()
        dt = parse_date(date_str)
        if dt:
            return dt
        cprint(RED, "   ❌ Format tidak dikenali, coba lagi.")

def get_time_input():
    """Minta input waktu dari user."""
    cprint(CYAN, "\n⏰ Masukkan jam commit (opsional):")
    cprint(YELLOW, "   Format: HH:MM  (24 jam) | Kosongkan untuk pakai 12:00")
    time_str = input("   Jam [12:00]: ").strip()
    if not time_str:
        return datetime.strptime("12:00", "%H:%M")
    t = parse_time(time_str)
    if t:
        return t
    cprint(YELLOW, "   ⚠️  Format salah, pakai 12:00 sebagai default.")
    return datetime.strptime("12:00", "%H:%M")

def get_message_input():
    """Minta pesan commit."""
    cprint(CYAN, "\n✏️  Pesan commit:")
    cprint(YELLOW, "   Kosongkan untuk pakai: 'Update'")
    msg = input("   Pesan: ").strip()
    return msg if msg else "Update"

def get_file_content():
    """Tanya konten file yang akan dibuat/diubah."""
    cprint(CYAN, "\n📄 Isi file commit (opsional):")
    cprint(YELLOW, "   File kecil akan dibuat/diperbarui untuk commit ini.")
    cprint(YELLOW, "   Kosongkan untuk pakai konten default.")
    content = input("   Konten [auto]: ").strip()
    return content

def make_backdated_commit(commit_date: datetime, message: str, file_content: str):
    """Buat file, stage, dan commit dengan tanggal mundur."""
    
    # Format tanggal untuk Git
    date_str = commit_date.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Nama file log
    log_file = ".git_backdate_log.md"
    
    # Tulis/append ke file log
    timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {commit_date.strftime('%Y-%m-%d %H:%M')} — {message}\n"
    entry += f"_{file_content if file_content else 'auto-generated entry'}_\n"
    entry += f"<!-- logged: {timestamp_now} -->\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # Git add
    subprocess.run(["git", "add", log_file], check=True)
    
    # Git commit dengan backdate
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"]    = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    
    result = subprocess.run(
        ["git", "commit", "-m", message],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        cprint(GREEN, f"\n✅ Commit berhasil!")
        cprint(GREEN, f"   📅 Tanggal : {commit_date.strftime('%A, %d %B %Y — %H:%M')}")
        cprint(GREEN, f"   ✏️  Pesan   : {message}")
    else:
        cprint(RED, "\n❌ Commit gagal:")
        print(result.stderr)
        return False
    return True

def push_to_github():
    """Push ke GitHub."""
    cprint(CYAN, "\n🚀 Push ke GitHub?")
    ans = input("   Ketik 'y' untuk push, lainnya untuk skip: ").strip().lower()
    if ans == 'y':
        cprint(YELLOW, "   Memilih branch...")
        
        # Deteksi branch aktif
        branch_result = subprocess.run(["git", "branch", "--show-current"],
                                        capture_output=True, text=True)
        branch = branch_result.stdout.strip() or "main"
        cprint(YELLOW, f"   Branch: {branch}")
        
        result = subprocess.run(
            ["git", "push", "origin", branch, "--force-with-lease"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            cprint(GREEN, "✅ Push berhasil! Cek GitHub-mu dalam beberapa menit 🟩")
        else:
            cprint(YELLOW, "⚠️  Push biasa gagal, coba --force...")
            result2 = subprocess.run(
                ["git", "push", "origin", branch, "--force"],
                capture_output=True, text=True
            )
            if result2.returncode == 0:
                cprint(GREEN, "✅ Push berhasil (force)! 🟩")
            else:
                cprint(RED, "❌ Push gagal:")
                print(result2.stderr)
                cprint(YELLOW, "\n💡 Tips: Pastikan kamu sudah login GitHub CLI atau SSH key sudah dikonfigurasi.")

def show_log():
    """Tampilkan beberapa commit terakhir."""
    cprint(CYAN, "\n📜 5 Commit terakhir:")
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%C(yellow)%h%Creset %C(green)%ad%Creset %s",
         "--date=format:%Y-%m-%d %H:%M", "-5"],
        capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"   {line}")
    else:
        print("   (belum ada commit)")

def add_more():
    """Tanya apakah mau tambah commit lagi."""
    print()
    ans = input("➕ Tambah commit mundur lagi? (y/n): ").strip().lower()
    return ans == 'y'

# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main():
    header()
    
    cprint(YELLOW, "📂 Pastikan kamu sudah masuk ke folder repo-mu.")
    cprint(YELLOW, "   Contoh: cd /path/ke/repo-kamu\n")
    
    check_git_repo()
    check_remote()
    
    print()
    cprint(BOLD, "─" * 44)
    cprint(BOLD + GREEN, " MULAI BUAT COMMIT MUNDUR")
    cprint(BOLD, "─" * 44)
    
    total = 0
    while True:
        # Input tanggal & waktu
        dt_date = get_date_input()
        dt_time = get_time_input()
        commit_date = dt_date.replace(hour=dt_time.hour, minute=dt_time.minute)
        
        # Pesan commit
        message = get_message_input()
        
        # Konten file (opsional)
        file_content = get_file_content()
        
        # Buat commit
        ok = make_backdated_commit(commit_date, message, file_content)
        if ok:
            total += 1
        
        if not add_more():
            break
    
    show_log()
    
    cprint(BOLD, "\n─" * 44)
    cprint(GREEN + BOLD, f" Total {total} commit berhasil dibuat!")
    cprint(BOLD, "─" * 44)
    
    push_to_github()
    
    print()
    cprint(GREEN, "🎉 Selesai! GitHub contribution graph-mu akan segera hijau 🟩")
    cprint(YELLOW, "   (GitHub biasanya butuh 1–5 menit untuk update graph-nya)")
    print()

if __name__ == "__main__":
    main()