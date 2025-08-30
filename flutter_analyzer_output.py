import subprocess
import os
import time
import shutil

def find_flutter_executable():
    """Mencari lokasi executable flutter."""
    # Coba cari flutter di PATH
    flutter_path = shutil.which('flutter')
    if flutter_path:
        return flutter_path
    
    # Jika tidak ditemukan di PATH, coba lokasi umum Flutter
    common_paths = [
        os.path.expanduser('~/flutter/bin/flutter'),
        os.path.expanduser('~/AppData/Local/Pub/Cache/bin/flutter'),
        'C:/flutter/bin/flutter',
        'C:/flutter/bin/flutter.exe',
        os.path.expanduser('~/flutter/bin/flutter.exe'),
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return None

def run_flutter_analyze():
    """Menjalankan perintah 'flutter analyze' dan menyimpan output ke file."""
    print("🔍 Memeriksa ketersediaan Flutter SDK...")
    
    # Cari executable flutter
    flutter_executable = find_flutter_executable()
    
    if not flutter_executable:
        print("❌ ERROR: Perintah 'flutter' tidak ditemukan di PATH atau lokasi umum.")
        print("\n💡 SOLUSI:")
        print("1. Pastikan Flutter SDK sudah diinstall")
        print("2. Tambahkan Flutter ke PATH sistem Anda")
        print("3. Restart terminal/command prompt setelah menambahkan PATH")
        print("4. Atau jalankan script ini dari terminal yang sudah memiliki akses Flutter")
        return False
    
    print(f"✅ Flutter ditemukan di: {flutter_executable}")
    print("\n🔄 Menjalankan flutter analyze...")
    
    try:
        # Menjalankan perintah flutter analyze dari root project (parent directory dari script)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [flutter_executable, 'analyze'], 
            text=True, 
            capture_output=True,
            cwd=project_root  # Jalankan dari root project, bukan dari folder script
        )
        
        # Gabungkan stdout dan stderr untuk output lengkap
        full_output = ""
        if result.stdout:
            full_output += result.stdout
        if result.stderr:
            if full_output:
                full_output += "\n" + "="*50 + "\nSTDERR:\n" + "="*50 + "\n"
            full_output += result.stderr
        
        # Jika tidak ada output, beri pesan default
        if not full_output.strip():
            full_output = "No issues found by flutter analyze."
        
        # Tambahkan timestamp dan informasi eksekusi
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        header = f"""Flutter Analyze Report
Generated: {timestamp}
Command: {flutter_executable} analyze
Working Directory: {project_root}
Return Code: {result.returncode}

{'='*60}
ANALYSIS RESULTS:
{'='*60}

"""
        
        final_output = header + full_output
        
        # Dapatkan directory tempat script berada
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Tulis ke file di directory yang sama dengan script (akan replace jika sudah ada)
        output_file = os.path.join(script_dir, "flutter_analyze.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_output)
        
        print(f"✅ Analisis selesai! Output disimpan ke: {output_file}")
        print(f"📊 Return code: {result.returncode}")
        
        # Tampilkan ringkasan
        if result.returncode == 0:
            print("🎉 Tidak ada masalah ditemukan!")
        else:
            print("⚠️ Ditemukan masalah dalam kode. Lihat file untuk detail lengkap.")
        
        # Tampilkan beberapa baris pertama sebagai preview
        lines = full_output.strip().split('\n')
        if len(lines) > 0:
            print(f"\n📋 Preview (5 baris pertama):")
            for i, line in enumerate(lines[:5]):
                print(f"   {line}")
            if len(lines) > 5:
                print(f"   ... dan {len(lines) - 5} baris lainnya")
        
        return True
        
    except FileNotFoundError:
        print("❌ ERROR: Perintah 'flutter' tidak ditemukan.")
        print("💡 SOLUSI: Pastikan Flutter SDK sudah diinstall dan PATH sudah dikonfigurasi.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Perintah gagal dengan return code {e.returncode}")
        if e.stderr:
            print(f"📋 Detail error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"❌ Terjadi error yang tidak terduga: {e}")
        return False

def main():
    """Fungsi utama program."""
    print("🚀 Flutter Analyzer - Menyimpan hasil analisis ke file")
    print("="*55)
    
    success = run_flutter_analyze()
    
    if success:
        print("\n✨ Program selesai dengan sukses!")
    else:
        print("\n💥 Program gagal dijalankan.")
    
    print("\n👋 Terima kasih telah menggunakan Flutter Analyzer!")

if __name__ == "__main__":
    main()
