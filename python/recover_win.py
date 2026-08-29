#!/usr/bin/env python3
example = """
Silinmiş dosya kurtarma
Yönetici olarak çalıştırılmalısınız.

Örnek: python recover_win.py \\.\D: C:\kurtarilan
"""

import sys
import time
from pathlib import Path
from datetime import datetime

SIGNATURES = {
    "jpg": {
        "headers": [b"\xFF\xD8\xFF"],
        "footer": b"\xFF\xD9",
        "max_size": 80 * 1024 * 1024,
    },
    "png": {
        "headers": [b"\x89PNG\r\n\x1a\n"],
        "footer": b"IEND\xaeB`\x82",
        "max_size": 80 * 1024 * 1024,
    },
    "gif": {
        "headers": [b"GIF87a", b"GIF89a"],
        "footer": b"\x00\x3B",
        "max_size": 30 * 1024 * 1024,
    },
    "bmp": {
        "headers": [b"BM"],
        "footer": None,
        "max_size": 50 * 1024 * 1024,
    },
    "pdf": {
        "headers": [b"%PDF"],
        "footer": b"%%EOF",
        "max_size": 150 * 1024 * 1024,
    },
    "mp4": {
        "headers": [b"ftyp"],
        "footer": None,
        "max_size": 1024 * 1024 * 1024,
    },
    "mov": {
        "headers": [b"ftypqt"],
        "footer": None,
        "max_size": 1024 * 1024 * 1024,
    },
    "avi": {
        "headers": [b"RIFF"],
        "footer": None,
        "max_size": 1024 * 1024 * 1024,
    },
    "zip": {
        "headers": [b"PK\x03\x04"],
        "footer": b"PK\x05\x06",
        "max_size": 300 * 1024 * 1024,
    },
}

def human_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def carve(data, offset, sig, ext, out_dir, counter):
    for header in sig["headers"]:
        if data.startswith(header, offset):
            start = offset
            max_end = min(len(data), start + sig["max_size"])

            if sig["footer"]:
                pos = data.find(sig["footer"], start + len(header), max_end)
                end = pos + len(sig["footer"]) if pos != -1 else max_end
            else:
                end = max_end

            content = data[start:end]
            if len(content) < 300:
                return None

            filename = out_dir / f"{ext}_{counter:06d}.{ext}"
            try:
                with open(filename, "wb") as f:
                    f.write(content)
                return filename, len(content)
            except Exception:
                return None
    return None

def scan_disk(source, output_dir, chunk_size=8 * 1024 * 1024):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(" WINDOWS FILE CARVING - SİLİNMİŞ DOSYA KURTARMA")
    print("=" * 65)
    print(f" Kaynak       : {source}")
    print(f" Çıktı klasörü: {out.resolve()}")
    print(f" Başlangıç    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    counter = 0
    stats = {ext: 0 for ext in SIGNATURES}
    total_size_recovered = 0
    start_time = time.time()

    try:
        # Windows'ta fiziksel disk açma
        with open(source, "rb") as f:
            # Boyutu öğrenmeye çalış
            try:
                f.seek(0, 2)
                total_size = f.tell()
                f.seek(0)
            except:
                total_size = 0
                print("[!] Disk boyutu alınamadı, yine de taranacak...")

            if total_size > 0:
                print(f" Toplam boyut : {human_size(total_size)}")
            print(" Tarama başladı...\n")

            position = 0
            overlap = 64 * 1024

            while True:
                f.seek(position)
                chunk = f.read(chunk_size + overlap)
                if not chunk:
                    break

                for ext, sig in SIGNATURES.items():
                    for header in sig["headers"]:
                        search = 0
                        while True:
                            idx = chunk.find(header, search)
                            if idx == -1:
                                break
                            result = carve(chunk, idx, sig, ext, out, counter)
                            if result:
                                fname, size = result
                                counter += 1
                                stats[ext] += 1
                                total_size_recovered += size
                                print(f"[+] {fname.name:<22} {human_size(size)}")
                            search = idx + 1

                position += chunk_size

                if total_size > 0:
                    percent = min(100.0, (position / total_size) * 100)
                    elapsed = time.time() - start_time
                    speed = (position / (1024*1024)) / elapsed if elapsed > 0 else 0
                    print(f"\r İlerleme: {percent:5.1f}% | Kurtarılan: {counter:4d} | "
                          f"Hız: {speed:5.1f} MB/s | Geçen: {int(elapsed)}s   ", end="", flush=True)
                else:
                    print(f"\r Okunan: {human_size(position)} | Kurtarılan: {counter}   ", end="", flush=True)

                # Çok büyük disklerde sonsuz döngüyü engelle
                if total_size > 0 and position >= total_size:
                    break
                if total_size == 0 and position > 2 * 1024**4:  # 2 TB güvenlik sınırı
                    break

    except PermissionError:
        print("\n\n[!] YETKİ HATASI!")
        print("Çözümler:")
        print("1. CMD veya PowerShell'i 'Yönetici olarak çalıştır' ile aç")
        print("2. Antivirus'ü geçici kapat (özellikle Windows Defender)")
        print("3. Doğru disk numarasını kullan (PhysicalDrive0, PhysicalDrive1...)")
        print("4. En güvenlisi: Disk imajı alıp imajı tara")
        return
    except OSError as e:
        print(f"\n\n[!] OS Hatası: {e}")
        print("Disk meşgul olabilir veya yanlış yol kullandın.")
        return
    except KeyboardInterrupt:
        print("\n\n[!] Kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\n\n[!] Beklenmeyen hata: {type(e).__name__}: {e}")
        return

    elapsed = time.time() - start_time
    print("\n\n" + "=" * 65)
    print(" TARAMA BİTTİ")
    print("=" * 65)
    print(f" Toplam süre           : {int(elapsed)} saniye")
    print(f" Kurtarılan dosya      : {counter}")
    print(f" Toplam kurtarılan boyut: {human_size(total_size_recovered)}")
    print("\n Türlere göre dağılım:")
    for ext, count in stats.items():
        if count > 0:
            print(f"   {ext.upper():6} → {count} adet")
    print(f"\n Dosyalar burada → {out.resolve()}")
    print("=" * 65)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(example)
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2]
    scan_disk(source, output)
