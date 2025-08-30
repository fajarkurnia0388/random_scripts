import subprocess
import os
import time
import threading
import shutil

# Event ini berfungsi sebagai "saklar" untuk menghentikan thread dengan aman
stop_event = threading.Event()

def find_dart_executable():
    """Mencari lokasi executable dart."""
    # Coba cari dart di PATH
    dart_path = shutil.which('dart')
    if dart_path:
        return dart_path
    
    # Jika tidak ditemukan di PATH, coba lokasi umum Flutter
    common_paths = [
        os.path.expanduser('~/flutter/bin/dart'),
        os.path.expanduser('~/AppData/Local/Pub/Cache/bin/dart'),
        'C:/flutter/bin/dart',
        'C:/flutter/bin/dart.exe',
        os.path.expanduser('~/flutter/bin/dart.exe'),
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return None

def run_dart_fix():
    """Menjalankan perintah 'dart fix --apply' dan menangani output."""
    try:
        # Cari executable dart
        dart_executable = find_dart_executable()
        
        if not dart_executable:
            print("\n❌ ERROR: Perintah 'dart' tidak ditemukan di PATH atau lokasi umum.")
            print("💡 SOLUSI: Pastikan Flutter SDK sudah diinstall dan ditambahkan ke PATH sistem.")
            print("   Atau jalankan script ini dari terminal yang sudah memiliki akses ke Flutter.")
            stop_event.set()
            return False
        
        # Menjalankan perintah dengan path absolut
        result = subprocess.run(
            [dart_executable, 'fix', '--apply'], 
            check=True, 
            text=True, 
            capture_output=True,
            cwd=os.getcwd()  # Pastikan working directory benar
        )
        
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Perbaikan otomatis berhasil diterapkan.")
        
        # Tampilkan output jika ada perubahan
        if result.stdout.strip():
            print(f"   📝 Output: {result.stdout.strip()}")
            
        return True
        
    except FileNotFoundError:
        print("\n❌ ERROR: Perintah 'dart' tidak ditemukan.")
        print("💡 SOLUSI: Pastikan Flutter SDK sudah diinstall dan PATH sudah dikonfigurasi.")
        stop_event.set()
        return False
    except subprocess.CalledProcessError as e:
        # Hanya tampilkan error jika perintah gagal
        print(f"\n[{time.strftime('%H:%M:%S')}] ❌ ERROR: Perintah gagal.")
        if e.stderr:
            print(f"   📋 Detail error: {e.stderr.strip()}")
        if e.stdout:
            print(f"   📋 Output: {e.stdout.strip()}")
        return False
    except Exception as e:
        print(f"\n[{time.strftime('%H:%M:%S')}] ❌ Terjadi error yang tidak terduga: {e}")
        return False

def run_periodically(interval_seconds):
    """
    Fungsi utama yang akan dijalankan di thread terpisah.
    Ini akan memanggil run_dart_fix() berulang kali.
    """
    print(f"\n--- 🚀 Memulai mode otomatis ---")
    print(f"Perintah akan dijalankan setiap {interval_seconds} detik.")
    
    while not stop_event.is_set():
        run_dart_fix()
        # Tunggu selama interval yang ditentukan atau sampai sinyal stop diterima
        stop_event.wait(interval_seconds)
        
    print("\n--- 🛑 Mode otomatis dihentikan ---")

def main():
    """Fungsi utama untuk setup dan menunggu perintah stop."""
    print("🔍 Memeriksa ketersediaan Dart SDK...")
    
    # Test dart executable terlebih dahulu
    dart_executable = find_dart_executable()
    if dart_executable:
        print(f"✅ Dart ditemukan di: {dart_executable}")
    else:
        print("❌ Dart tidak ditemukan!")
        print("\n💡 SOLUSI:")
        print("1. Pastikan Flutter SDK sudah diinstall")
        print("2. Tambahkan Flutter ke PATH sistem Anda")
        print("3. Restart terminal/command prompt setelah menambahkan PATH")
        print("4. Atau jalankan script ini dari terminal yang sudah memiliki akses Flutter")
        return
    
    try:
        interval = int(input("\nAtur interval waktu dalam detik (contoh: 10): "))
        if interval <= 0:
            print("⚠️ Interval harus lebih dari 0.")
            return
    except ValueError:
        print("⚠️ Input tidak valid. Harap masukkan angka.")
        return

    # Buat dan mulai thread yang akan menjalankan tugas di latar belakang
    background_thread = threading.Thread(target=run_periodically, args=(interval,))
    background_thread.start()

    # Main thread akan menunggu di sini sampai pengguna menekan Enter
    print("\n=======================================================")
    print("   Program berjalan di latar belakang...")
    print("   Tekan [ENTER] kapan saja untuk menghentikan program.")
    print("=======================================================")
    input() # Baris ini akan menjeda program sampai Enter ditekan

    # Setelah Enter ditekan, kirim sinyal stop ke thread
    stop_event.set()

    # Tunggu thread selesai dengan rapi sebelum keluar dari program utama
    background_thread.join()
    print("👋 Program ditutup.")

if __name__ == "__main__":
    main()
