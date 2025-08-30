import subprocess
import os
import shutil

def find_flutter_executable():
    """Mencari lokasi executable flutter."""
    flutter_path = shutil.which('flutter')
    if flutter_path:
        return flutter_path
    
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

def run_flutter_test():
    """Menjalankan perintah 'flutter test' dan menyimpan output ke file."""
    print("🔍 Memeriksa ketersediaan Flutter SDK...")
    
    flutter_executable = find_flutter_executable()
    
    if not flutter_executable:
        print("❌ ERROR: Perintah 'flutter' tidak ditemukan di PATH atau lokasi umum.")
        return False
    
    print(f"✅ Flutter ditemukan di: {flutter_executable}")
    print("\n🔄 Menjalankan flutter test...")
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            [flutter_executable, 'test', '--coverage'], 
            text=True, 
            capture_output=True,
            cwd=project_root
        )
        
        full_output = ""
        if result.stdout:
            full_output += result.stdout
        if result.stderr:
            if full_output:
                full_output += "\n" + "="*50 + "\nSTDERR:\n" + "="*50 + "\n"
            full_output += result.stderr
        
        if not full_output.strip():
            full_output = "No issues found by flutter test."
        
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flutter_test_results.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_output)
        
        print(f"✅ Pengujian selesai! Output disimpan ke: {output_file}")
        print(f"📊 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("🎉 Tidak ada masalah ditemukan!")
        else:
            print("⚠️ Ditemukan masalah dalam kode. Lihat file untuk detail lengkap.")
        
        return True
        
    except FileNotFoundError:
        print("❌ ERROR: Perintah 'flutter' tidak ditemukan.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Perintah gagal dengan return code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Terjadi error yang tidak terduga: {e}")
        return False

def main():
    """Fungsi utama program."""
    print("🚀 Flutter Tester - Menyimpan hasil pengujian ke file")
    print("="*55)
    
    success = run_flutter_test()
    
    if success:
        print("\n✨ Program selesai dengan sukses!")
    else:
        print("\n💥 Program gagal dijalankan.")
    
    print("\n👋 Terima kasih telah menggunakan Flutter Tester!")

if __name__ == "__main__":
    main()
