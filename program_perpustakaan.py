import json
import os
import hashlib
from datetime import datetime, timedelta,timezone

WIB = timezone(timedelta(hours=7))
DATABASE_FILE = "database.json"
DEFAULT_LOAN_DAYS = 7  # atau sesuaikan
users = []
# ============================================================
# FUNGSI BANTU
# ============================================================
def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_dt(dt_str):
    # jika None -> "-"
    return dt_str if dt_str else "-"

# ============================================================
# LOAD & SAVE DATA
# ============================================================
def load_data():
    # Define a default structure to ensure all keys exist and have correct initial types
    initial_data = {
        "books": [],
        "users": [],
        "transactions": []
    }
    
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                # Load existing data
                existing_data = json.load(f)
                
                # Update initial_data with existing data
                # This ensures keys present in existing_data override initial_data
                initial_data.update(existing_data)
                
                # Crucially, ensure 'users' is a list, even if it was loaded as a dict
                if not isinstance(initial_data["users"], list):
                    print("Warning: 'users' data was not a list, converting to an empty list.")
                    initial_data["users"] = []
                    
        except json.JSONDecodeError:
            print("Warning: database.json is corrupted or empty. Starting with default empty database.")
    
    return initial_data

def save_data(data):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ============================================================
# MEMBUAT ADMIN DEFAULT (HANYA JIKA BELUM ADA USER)
# ============================================================
# def create_default_admin():
#     if len(data["users"]) == 0:
#         admin = {
#             "user_id": 1,
#             "name": "Admin",
#             "pin_hash": hash_pin("1234"),   # PIN default 1234
#             "role": "admin"
#         }
#         data["users"].append(admin)
#         save_data(data)
#         print("Admin default berhasil dibuat! (PIN: 1234)")

# create_default_admin()

# ============================================================
# LOGIN
# ============================================================
def login():
    print("\n=== LOGIN ===")
    username = input("Nama: ").strip()
    pin = input("PIN: ").strip()

    for u in data["users"]:
        if u["name"].lower() == username.lower():
            if u["pin_hash"] == hash_pin(pin):
                print(f"\nLogin berhasil! Selamat datang, {u['name']}.\n")
                return u  # Return seluruh data user
            else:
                print("PIN salah!")
                return None

    print("User tidak ditemukan!")
    return None

# ============================================================
# TAMBAH USER (ADMIN)
# ============================================================
def tambah_user():
    print("\n=== TAMBAH USER ===")
    name = input("Nama user baru: ").strip()
    if not name:
        print("Nama kosong.")
        return
    pin = input("PIN user (angka): ").strip()
    if not pin.isdigit():
        print("PIN harus angka.")
        return
    role = input("Role (admin/user) [user]: ").strip().lower()
    if role not in ("admin","user",""):
        print("Role invalid. Menggunakan 'user'.")
        role = "user"
    role = role if role else "user"

    new_id = max([u.get("user_id",0) for u in data["users"]], default=0) + 1
    user = {
        "user_id": new_id,
        "name": name,
        "pin_hash": hash_pin(pin),
        "role": role
    }

    data["users"].append(user)
    save_data(data)
    print(f"User baru berhasil ditambahkan! user_id={new_id}\n")

# ============================================================
# FITUR BUKU (dengan timestamp)
# ============================================================
def tambah_buku():
    title = input("Judul buku: ").strip()
    author = input("Penulis: ").strip()
    category = input("Kategori: ").strip()

    new_id = max([b.get("id",0) for b in data["books"]], default=0) + 1

    book = {
        "id": new_id,
        "title": title or "Untitled",
        "author": author or "Unknown",
        "category": category or "Umum",
        "status": "available",
        "borrowed_by": None,
        "borrowed_date": None,   # now will store "YYYY-MM-DD HH:MM:SS"
        "due_date": None         # same format with time
    }

    data["books"].append(book)
    save_data(data)
    print("Buku berhasil ditambahkan!\n")

def tampilkan_buku():
    print("\n=== DAFTAR BUKU ===")
    if not data["books"]:
        print("Belum ada buku.")
        return
    for b in data["books"]:
        if b["status"] == "borrowed":
            borrowed_by = b.get("borrowed_by") or "-"
            borrowed_date = format_dt(b.get("borrowed_date"))
            due_date = format_dt(b.get("due_date"))
            #  "Even" if number % 2 == 0 else "Odd"
            print(f"[{b['id']}] {b['title']} - {b['author']} | {( "Dipinjam" if b['status'] == 'borrowed' else "tersedia")} | dipinjam oleh: {borrowed_by} | pinjam: {borrowed_date} | due: {due_date}")
        else:
            print(f"[{b['id']}] {b['title']} - {b['author']} | {( "Dipinjam" if b['status'] == 'borrowed' else "tersedia")}")
    print()

def pinjam_buku(user):
    tampilkan_buku()
    try:
        book_id = int(input("ID buku yang dipinjam: ").strip())
    except:
        print("ID invalid.")
        return

    for b in data["books"]:
        if b["id"] == book_id:
            if b["status"] == "borrowed":
                print("Buku sedang dipinjam orang lain!")
                return

            # ambil waktu sekarang
            borrow_dt = datetime.now(WIB)
            due_dt = borrow_dt + timedelta(days=DEFAULT_LOAN_DAYS)

            b["status"] = "borrowed"
            b["borrowed_by"] = user["name"]
            b["borrowed_date"] = borrow_dt.strftime("%Y-%m-%d %H:%M:%S")
            b["due_date"] = due_dt.strftime("%Y-%m-%d %H:%M:%S")

            # simpan transaksi
            tx_id = len(data.get("transactions",[])) + 1
            data.setdefault("transactions", []).append({
                "tx_id": tx_id,
                "type": "borrow",
                "book_id": b["id"],
                "user_name": user["name"],
                "borrowed_at": b["borrowed_date"],
                "due_at": b["due_date"],
                "returned_at": None
            })

            save_data(data)

            # --- tampilkan jam secara terpisah ---
            print("\nBuku berhasil dipinjam!")
            print(f"Judul       : {b['title']}")
            print(f"Peminjam    : {user['name']}")
            print(f"Tanggal     : {borrow_dt.strftime('%Y-%m-%d')}")
            print(f"Jam Pinjam  : {borrow_dt.strftime('%H:%M:%S')}")
            print(f"Jatuh Tempo : {due_dt.strftime('%Y-%m-%d')}")
            print(f"Jam Jatuh   : {due_dt.strftime('%H:%M:%S')}\n")
            return

    print("ID buku tidak ditemukan.")

def kembalikan_buku(user):
    tampilkan_buku()
    try:
        book_id = int(input("ID buku yang dikembalikan: ").strip())
    except:
        print("ID invalid.")
        return

    for b in data["books"]:
        if b["id"] == book_id:
            if b["status"] != "borrowed":
                print("Buku ini tidak sedang dipinjam.")
                return
            # hanya peminjam atau admin boleh mengembalikan
            if b["borrowed_by"] != user["name"] and user["role"] != "admin":
                print("Hanya peminjam asli atau admin yang dapat mengembalikan buku ini.")
                return

            returned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # update transaksi terakhir untuk buku ini (jika ada)
            for tx in reversed(data.get("transactions", [])):
                if tx.get("book_id") == book_id and tx.get("type") == "borrow" and tx.get("returned_at") is None:
                    tx["returned_at"] = returned_at
                    break

            b["status"] = "available"
            b["borrowed_by"] = None
            b["borrowed_date"] = None
            b["due_date"] = None
            save_data(data)
            print(f"Buku [{book_id}] berhasil dikembalikan. Waktu kembali: {returned_at}\n")
            return

    print("ID buku tidak ditemukan.")

def hapus_buku():
    print("\n=== HAPUS BUKU ===")
    tampilkan_buku()

    try:
        book_id = int(input("Masukkan ID buku yang akan dihapus: "))
    except:
        print("ID tidak valid!")
        return

    for b in data["books"]:
        if b["id"] == book_id:
            if b["status"] == "borrowed":
                print("Tidak bisa menghapus buku yang sedang dipinjam!")
                return

            data["books"].remove(b)
            save_data(data)
            print("Buku berhasil dihapus!\n")
            return

    print("ID buku tidak ditemukan!\n")
def hapus_user():
    print("\n=== HAPUS USER ===")
    for u in data["users"]:
        print(f"[{u['user_id']}] {u['name']} - {u['role']}")

    try:
        uid = int(input("Masukkan ID user yang akan dihapus: "))
    except:
        print("ID tidak valid!")
        return

    for u in data["users"]:
        if u["user_id"] == uid:

            if u["role"] == "admin":
                print("Admin tidak boleh dihapus!")
                return

            # pastikan user tidak sedang meminjam buku
            for b in data["books"]:
                if b["borrowed_by"] == u["name"]:
                    print("User ini sedang meminjam buku. Tidak bisa dihapus!")
                    return

            data["users"].remove(u)
            save_data(data)
            print("User berhasil dihapus!\n")
            return

    print("User tidak ditemukan!\n")

def hapus_semua_user():   # 🔥 fitur baru
    konfirmasi = input("Yakin ingin menghapus SEMUA USER? (y/n): ").lower()
    if konfirmasi == "y":
        data["users"]=[] # Fixed: Changed from {} to []
        save_data(data)
        print("SEMUA user berhasil dihapus!")
    else:
        print("Dibatalkan.")
def hapus_transaksi():
    print("\n=== HAPUS TRANSAKSI ===")

    if len(data.get("transactions", [])) == 0:
        print("Belum ada transaksi.")
        return

    for t in data["transactions"]:
        print(f"[{t['tx_id']}] {t['type']} - Buku {t['book_id']} - {t['user_name']}")

    try:
        tx_id = int(input("Masukkan ID transaksi yang akan dihapus: "))
    except:
        print("ID tidak valid!")
        return

    for t in data["transactions"]:
        if t["tx_id"] == tx_id:
            data["transactions"].remove(t)
            save_data(data)
            print("Transaksi berhasil dihapus!\n")
            return

    print("Transaksi tidak ditemukan!\n")


# ============================================================
# MENU UTAMA
# ============================================================
def menu_utama(user):
    while True:
        print("=== MENU UTAMA ===")
        print("1. Tambah Buku (admin)")
        print("2. Tampilkan Buku")
        print("3. Pinjam Buku")
        print("4. Kembalikan Buku")
        print("5. Tambah User (admin)")
        print("6. Hapus Buku (admin)")
        print("7. Hapus User (admin)")
        print("8. Hapus Semua User (admin)")
        print("9. Hapus Transaksi (admin)")
        print("10. Keluar")
        print("11. Logout")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            if user["role"] == "admin":
                tambah_buku()
            else:
                print("Akses ditolak!")
        elif pilihan == "2":
            tampilkan_buku()
        elif pilihan == "3":
            pinjam_buku(user)
        elif pilihan == "4":
            kembalikan_buku(user)
        elif pilihan == "5":
            if user["role"] == "admin":
                tambah_user()
            else:
                print("Akses ditolak!")
        elif pilihan == "6":
            if user["role"] == "admin":
                hapus_buku()
            else:
                print("Akses ditolak!")
        elif pilihan == "7":
            if user["role"] == "admin":
                hapus_user()
            else:
                print("Akses ditolak!")
        elif pilihan == "8":
            if user["role"] == "admin":
                hapus_semua_user()
            else:
                print("Akses ditolak!")
        elif pilihan == "9":
            if user["role"] == "admin":
                hapus_transaksi()
            else:
                print("Akses ditolak!")
        elif pilihan == "10":
            print("Keluar...")
            break
        elif pilihan == "11":
            print("\nAnda telah logout.\n")
            return "logout"
        else:
            print("Pilihan tidak valid!")

def register_user():
    print("\n=== REGISTER USER ===")
    name = input("Nama: ").strip()

    # Cek jika nama sudah dipakai
    for u in data["users"]:
        if u["name"].lower() == name.lower():
            print("Nama sudah terdaftar! Silakan login.")
            return

    pin = input("PIN (angka): ").strip()
    if not pin.isdigit():
        print("PIN harus berupa angka!")
        return

    # Pilih role
    print("\nPilih Role:")
    print("1. admin")
    print("2. user")

    role_input = input("Masukkan pilihan role (1/2): ").strip()

    if role_input == "1":
        role = "admin"
    elif role_input == "2":
        role = "user"
    else:
        print("Pilihan role tidak valid! Default = user.")
        role = "user"

    new_id = max([u.get("user_id", 0) for u in data["users"]], default=0) + 1

    user = {
        "user_id": new_id,
        "name": name,
        "pin_hash": hash_pin(pin),
        "role": role
    }

    data["users"].append(user)
    save_data(data)

    print(f"\nRegistrasi berhasil!")
    print(f"Nama : {name}")
    print(f"Role : {role}")
    print("Silakan login.\n")

# ============================================================
# MAIN PROGRAM
# ============================================================
def main():
    print("=== SISTEM PERPUSTAKAAN ===")

    while True:
        print("\n=== MENU AWAL ===")
        print("1. Login")
        print("2. Register")
        print("3. Keluar")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            user = None
            while user is None:
                user = login()

            status = menu_utama(user)
            if status == "logout":
                continue

        elif pilihan == "2":
            register_user()

        elif pilihan == "3":
            print("Keluar...")
            break

        else:
            print("Pilihan tidak valid!")


if __name__ == "__main__":
    main()
