# MediCipher (Medical Data Encryption and Security System)

MediCipher adalah sistem aplikasi desktop pengelolaan dan pengamanan arsip hasil pemeriksaan laboratorium medis yang dibangun menggunakan bahasa pemrograman Python. Sistem ini dirancang untuk melindungi catatan hasil laboratorium, dokumen medis (PDF, DOCX, TXT), dan citra mikroskopis medis (PNG) menggunakan kombinasi algoritma kriptografi klasik dan modern, steganografi spasial (Least Significant Bit), kontrol akses multi-faktor (Username/Password, Biometrik Wajah Facenet512, dan USB Flashdisk Fisik sebagai Dongle Perangkat Keras), serta verifikasi integritas menggunakan konsep rantai blok (Simple Blockchain SHA-256 Hash Chain) dengan basis data MySQL.

---

## 1. TUJUAN APLIKASI

1. Menyediakan repositori lokal terenkripsi untuk menyimpan dan mengelola data catatan pemeriksaan medis laboratorium secara aman.
2. Mencegah kebocoran data sensitif pasien (nama, kode pasien, hasil diagnosa, catatan klinis) pada tingkat database menggunakan skema enkripsi terautentikasi (Authenticated Encryption).
3. Menerapkan kontrol akses berjenjang (3-Factor Authentication) yang mewajibkan kepemilikan kredensial, verifikasi wajah biologis langsung, dan token perangkat fisik USB.
4. Melindungi dokumen hasil lab dalam bentuk file biner mandiri (.medcipher) agar tidak dapat dibaca atau dimodifikasi pihak tidak berwenang saat didistribusikan.
5. Menyembunyikan pesan atau kode dokumen rahasia di dalam citra mikroskopis tanpa merusak interpretasi visual menggunakan steganografi LSB berenkripsi.
6. Menjamin imutabilitas dan mendeteksi pemalsuan berkas rekam medis melalui pembuktian rantai blok kriptografis SHA-256.

---

## 2. FITUR UTAMA

1. **Authentication & Multi-Factor Security (3FA)**
   - Registrasi otomatis saat pertama kali aplikasi dijalankan ketika database belum memiliki akun.
   - Lapisan 1: Verifikasi token perangkat USB fisik melalui Windows API (pembacaan serial volume dan file kunci MEDICIPHER_DEVICE.key).
   - Lapisan 2: Validasi username dan kata sandi menggunakan fungsi hash Argon2id (dengan proteksi brute-force lockout dan pencatatan audit log).
   - Lapisan 3: Verifikasi biometrik wajah langsung melalui webcam menggunakan Facenet512 (representasi 512 dimensi terenkripsi AES-256-GCM).
   - Pemantauan latar belakang (background thread): aplikasi otomatis mengunci sesi jika USB dongle dicabut saat digunakan.
   - Penguncian otomatis sesi tidak aktif (Inactivity Timeout).

2. **Medical Text Super Encryption**
   - Super enkripsi catatan medis: Vigenere Cipher dilanjutkan AES-128-ECB (PKCS7 padding) dan HMAC-SHA256.
   - Mempertahankan spasi, angka, dan tanda baca pada teks asli.
   - Serialisasi hasil enkripsi dalam format Base64.
   - Verifikasi integritas HMAC sebelum proses dekripsi dijalankan.

3. **Medical File Encryption (.medcipher)**
   - Pengamanan berkas laboratorium berformat PDF, DOCX, dan TXT.
   - Enkripsi AES-128-CBC dengan salt acak 16 byte dan IV acak 16 byte per operasi.
   - Penurunan kunci 48 byte menggunakan PBKDF2-HMAC-SHA256 (16 byte AES-128 + 32 byte HMAC-SHA256).
   - Integritas ciphertext diverifikasi dengan HMAC-SHA256 sebelum dekripsi.

4. **Secure Medical Database (MySQL)**
   - Penyimpanan data pemeriksaan medis dengan skema MySQL berbasis parameter (mencegah SQL Injection).
   - Enkripsi kolom sensitif (kode pasien, nama pasien, hasil, catatan) menggunakan AES-256-GCM (NIST SP 800-38D).
   - Pengelolaan Master Key lokal terproteksi Windows Data Protection API (DPAPI).
   - Penurunan subkunci spesifik fungsi menggunakan HKDF (RFC 5869) berbasis HMAC-SHA256.
   - Dekripsi data sensitif dilakukan secara dinamis hanya saat ditampilkan pada antarmuka aplikasi.

5. **Medical Image Steganography**
   - Penyisipan informasi rahasia ke dalam citra laboratorium berformat PNG dan JPG.
   - Pra-enkripsi pesan rahasia menggunakan AES-256-GCM sebelum disisipkan.
   - Metode Least Significant Bit (LSB) pada kanal warna RGB citra PNG dan JPG.
   - Validasi kapasitas citra sebelum proses penyisipan.
   - Menghasilkan file gambar stego baru tanpa merusak file gambar asli.

6. **Blockchain Verification**
   - Pencatatan aset berkas dan citra laboratorium ke dalam rantai blok lokal (Simple Blockchain).
   - Genesis Block diinisialisasi otomatis sebagai jangkar awal (index 0, previous hash 64 nol).
   - Blok baru dihubungkan melalui serialisasi data deterministik dan hash SHA-256.
   - Fitur verifikasi komprehensif: membandingkan hash berkas aktual dan memvalidasi keutuhan seluruh mata rantai (previous_hash link).
   - Status keluaran: VALID, INVALID (file termanipulasi), atau CHAIN INVALID (kerusakan buku besar blockchain).

7. **Dashboard & Security Audit**
   - Ringkasan metrik arsip, berkas aman, buku besar blok, dan status hardware USB.
   - Riwayat log aktivitas dan keamanan yang tersimpan secara terstruktur pada MySQL.

---

## 3. DAFTAR ALGORITMA KRIPTOGRAFI

| Algoritma | Peran dalam Sistem MediCipher |
|---|---|
| Argon2id | Fungsi hash satu arah untuk kredensial kata sandi pengguna |
| Vigenere Cipher | Tahap pertama super enkripsi teks catatan laboratorium medis |
| AES-128-ECB | Tahap kedua super enkripsi teks medis dengan padding PKCS7 |
| AES-128-CBC | Enkripsi dokumen berkas laboratorium (.medcipher) dengan IV acak |
| AES-256-GCM | Enkripsi data sensitif database MySQL, embedding wajah, dan payload steganografi |
| HMAC-SHA256 | Autentikasi integritas data super enkripsi teks dan berkas .medcipher |
| SHA-256 | Penghitungan hash berkas, hash token USB, dan mata rantai blok blockchain |
| PBKDF2-HMAC-SHA256 | Penurunan kunci enkripsi dan integritas dari passphrase pengguna |
| HKDF (RFC 5869) | Penurunan subkunci aplikasi dari Master Key lokal |
| Windows DPAPI | Proteksi penyimpanan Master Key pada sistem operasi Windows |
| Facenet512 | Ekstraksi fitur embedding biometrik wajah 512 dimensi |
| LSB (Least Significant Bit) | Penyisipan bit ciphertext ke kanal warna RGB citra PNG dan JPG |

---

## 4. TEKNOLOGI YANG DIGUNAKAN

- Bahasa Pemrograman: Python 3.10+ (Diuji pada Python 3.13)
- Antarmuka Desktop: CustomTkinter / Tkinter (Tema Dark Slate Modern)
- Basis Data: MySQL Server 8.0+ / MariaDB 10.4+ (XAMPP / Standalone)
- Driver Database: mysql-connector-python
- Pustaka Kriptografi: cryptography (pyca/cryptography) dengan mesin AES/GCM bawaan mandiri
- Pustaka Hash Kata Sandi: argon2-cffi
- Pengenalan Wajah: OpenCV (opencv-python) dan DeepFace (Facenet512)
- Pengolahan Gambar: Pillow (PIL)
- Antarmuka Windows API: Windows ctypes dan pywin32
- Manajemen Konfigurasi: python-dotenv
- Kerangka Kerja Pengujian: pytest dan Python unittest

---

## 5. STRUKTUR FOLDER PROYEK

```
MediCipher/
|-- main.py                      # Entri utama aplikasi desktop
|-- requirements.txt             # Daftar dependensi library Python
|-- .env.example                 # Contoh file konfigurasi environment
|-- .gitignore                   # Konfigurasi file yang diabaikan git
|-- README.md                    # Dokumentasi lengkap sistem
|
|-- config/
|   |-- __init__.py
|   |-- settings.py              # Pengaturan aplikasi, direktori, dan .env
|
|-- database/
|   |-- __init__.py
|   |-- connection.py            # Manajer koneksi MySQL
|   |-- schema.sql               # Skrip DDL inisialisasi tabel database
|   |-- migrations.py            # Skrip otomatisasi tabel dan cek first-run
|   |-- repository.py            # Akses query terparameterisasi dan transaksi
|
|-- authentication/
|   |-- __init__.py
|   |-- register.py              # Alur pendaftaran akun administrator awal
|   |-- login.py                 # Alur login 3FA dan SessionManager
|   |-- password.py              # Validasi dan hashing password Argon2id
|   |-- face_verification.py     # Perekaman & verifikasi wajah Facenet512
|   |-- usb_dongle.py            # Deteksi Windows API dan validasi USB fisik
|
|-- cryptography/
|   |-- __init__.py
|   |-- _aes_core.py             # Mesin AES murni (ECB, CBC, GCM, PKCS7)
|   |-- vigenere.py              # Implementasi Vigenere Cipher klasik
|   |-- aes_ecb.py               # Super enkripsi teks Vigenere + AES-ECB + HMAC
|   |-- aes_cbc.py               # Enkripsi dokumen berkas .medcipher
|   |-- aes_gcm.py               # Enkripsi terautentikasi AES-256-GCM
|   |-- key_manager.py           # Pengelola Master Key DPAPI dan HKDF
|   |-- hashing.py               # SHA-256, HMAC-SHA256, dan PasswordHasher
|
|-- steganography/
|   |-- __init__.py
|   |-- lsb.py                   # Penyisipan & ekstraksi LSB citra PNG
|
|-- blockchain/
|   |-- __init__.py
|   |-- block.py                 # Model struktur data blok SHA-256
|   |-- chain.py                 # Manajer buku besar blockchain terintegrasi MySQL
|
|-- modules/
|   |-- __init__.py
|   |-- medical_text.py          # Layanan bisnis super enkripsi teks
|   |-- medical_file.py          # Layanan bisnis enkripsi dokumen berkas
|   |-- medical_database.py      # Layanan bisnis rekam medis MySQL terenkripsi
|   |-- medical_image.py         # Layanan bisnis steganografi citra
|   |-- asset_verification.py    # Layanan bisnis verifikasi blockchain
|
|-- ui/
|   |-- __init__.py
|   |-- theme.py                 # Definisi warna, font, dan adapter CustomTkinter
|   |-- register_page.py         # Tampilan registrasi akun awal
|   |-- login_page.py            # Tampilan login tiga lapisan keamanan
|   |-- dashboard.py             # Tampilan dashboard metrik dan audit log
|   |-- text_encryption_page.py  # Tampilan super enkripsi teks
|   |-- file_encryption_page.py  # Tampilan enkripsi berkas dokumen
|   |-- medical_database_page.py # Tampilan manajemen arsip rekam medis
|   |-- steganography_page.py    # Tampilan steganografi citra PNG
|   |-- blockchain_page.py       # Tampilan pencatatan dan verifikasi blockchain
|   |-- settings_page.py         # Tampilan pengaturan sistem dan logout
|
|-- assets/                      # Direktori ikon dan aset statis
|-- storage/                     # Penyimpanan Master Key terproteksi DPAPI
|
|-- tests/                       # Unit test menyeluruh
|   |-- test_authentication.py   # Pengujian password, wajah, dan USB dongle
|   |-- test_vigenere.py         # Pengujian Vigenere Cipher
|   |-- test_aes_ecb.py          # Pengujian super enkripsi teks
|   |-- test_aes_cbc.py          # Pengujian enkripsi file .medcipher
|   |-- test_database.py         # Pengujian KeyManager DPAPI dan AES-256-GCM
|   |-- test_steganography.py    # Pengujian LSB citra PNG
|   |-- test_blockchain.py       # Pengujian blok dan rantai hash SHA-256
```

---

## 6. PERSYARATAN INSTALASI

- Sistem Operasi: Windows 10 atau Windows 11 (64-bit).
- Python: Versi 3.10 atau yang lebih baru.
- MySQL Server: MySQL 8.0+ atau MariaDB (misalnya melalui XAMPP Control Panel).
- Kamera: Webcam aktif (internal laptop atau USB webcam eksternal) untuk verifikasi wajah.
- Perangkat Keras: Minimal satu unit USB Flashdisk fisik untuk didaftarkan sebagai dongle aplikasi.

---

## 7. CARA MEMASANG DEPENDENSI

Buka terminal PowerShell atau Command Prompt pada direktori proyek MediCipher, lalu jalankan perintah:

```powershell
pip install -r requirements.txt
```

Jika menggunakan virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## 8. CARA MENYIAPKAN BASIS DATA MYSQL

1. Pastikan layanan MySQL sedang aktif (misalnya klik tombol Start pada modul MySQL di XAMPP Control Panel).
2. Salin file konfigurasi environment dari `.env.example` ke `.env`:

```powershell
copy .env.example .env
```

3. Sesuaikan parameter koneksi MySQL pada file `.env` jika password MySQL Anda berbeda:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=medicipher_db
```

4. Database `medicipher_db` beserta seluruh tabel relasional (`users`, `face_templates`, `dongle_devices`, `medical_records`, `medical_assets`, `blockchain_blocks`, `audit_logs`) akan otomatis dibuat oleh sistem migrasi saat aplikasi pertama kali dijalankan. Alternatif lain, Anda dapat mengimpor file `database/schema.sql` melalui phpMyAdmin atau MySQL CLI:

```powershell
mysql -u root -p < database/schema.sql
```

---

## 9. CARA MENJALANKAN APLIKASI

Jalankan perintah berikut pada terminal:

```powershell
python main.py
```

---

## 10. PANDUAN PENGGUNAAN SISTEM

### A. Registrasi Administrator Pertama Kali
1. Saat aplikasi dibuka pertama kali dan database MySQL belum memiliki data pengguna, sistem secara otomatis membuka halaman **REGISTRASI AWAL**.
2. Masukkan username (minimal 3 karakter alfanumerik) dan password (minimal 8 karakter dengan kombinasi huruf besar, huruf kecil, angka, dan simbol khusus).
3. Hubungkan USB Flashdisk fisik Anda ke port USB komputer.
4. Klik tombol **Pindai Ulang Drive**, lalu pilih USB Flashdisk Anda pada daftar pilihan drive.
5. Klik tombol **Ambil Sampel Wajah Melalui Kamera**. Posisikan wajah Anda tepat di depan webcam hingga muncul status konfirmasi ekstraksi embedding Facenet512.
6. Klik tombol **Selesaikan Pendaftaran Administrator**. Sistem akan:
   - Membuat token rahasia acak 32 byte dan menulis file `MEDICIPHER_DEVICE.key` pada root USB Flashdisk Anda.
   - Menyimpan hash SHA-256 token dan serial volume USB ke database MySQL.
   - Mengenkripsi embedding wajah dengan AES-256-GCM ke MySQL.
   - Menyimpan kredensial ber-hash Argon2id ke tabel `users`.
7. Setelah registrasi selesai, aplikasi mengarahkan Anda ke halaman Login.

### B. Alur Login Tiga Lapisan (3FA)
Setiap kali membuka aplikasi, seluruh tiga tahapan keamanan wajib dipenuhi:
1. **Lapisan 1 (USB Dongle):** Pastikan USB Flashdisk yang didaftarkan terhubung. Sistem memverifikasi serial volume dan kecocokan token fisik terhadap hash tersimpan di MySQL.
2. **Lapisan 2 (Kredensial):** Masukkan username dan password. Sistem memverifikasi kecocokan menggunakan Argon2id. Terdapat proteksi pembatasan percobaan gagal maksimal 5 kali.
3. **Lapisan 3 (Biometrik Wajah):** Klik tombol **Aktifkan Kamera & Verifikasi Wajah**. Sistem mengambil citra wajah langsung dari kamera, mengekstraksi embedding, dan membandingkannya dengan template terenkripsi menggunakan Cosine Distance (ambang batas jarak <= 0.30).
4. Klik tombol **Masuk ke Sistem MediCipher**. Jika ketiga lapisan berhasil, sesi pengguna dimulai dan dashboard terbuka.

### C. Penggunaan Fitur Super Enkripsi Teks Medis
1. Buka menu **Enkripsi Teks Medis** pada bilah navigasi kiri.
2. Masukkan catatan hasil pemeriksaan medis pada area teks atau klik **Muat Contoh Medis**.
3. Masukkan Kunci Vigenere (alfabet A-Z) dan Passphrase AES-128.
4. Klik **Jalankan Super Enkripsi**. Teks akan melalui Vigenere -> PKCS7 Padding -> AES-128-ECB -> HMAC-SHA256, lalu ditampilkan dalam format Base64.
5. Untuk dekripsi, masukkan ciphertext Base64, kunci Vigenere, dan passphrase AES, lalu klik **Jalankan Super Dekripsi**. Sistem memverifikasi keaslian HMAC sebelum memulihkan teks asli.

### D. Penggunaan Fitur Enkripsi Dokumen Berkas (.medcipher)
1. Buka menu **Enkripsi Dokumen File**.
2. Pada panel kiri, klik **Pilih Berkas Dokumen** (mendukung PDF, DOCX, TXT).
3. Masukkan passphrase enkripsi, lalu klik **Enkripsi ke Format .medcipher**.
4. Simpan file hasil enkripsi. Setiap file diproteksi salt 16 byte acak, IV 16 byte acak, AES-128-CBC, dan autentikasi HMAC-SHA256.
5. Untuk memulihkan dokumen, pilih file `.medcipher` pada panel kanan, masukkan passphrase, lalu klik **Verifikasi HMAC & Dekripsi File**.

### E. Penggunaan Basis Data Medis Terenkripsi
1. Buka menu **Database Medis Aman**.
2. Isi formulir ID Pemeriksaan, Kode Pasien, Nama Pasien, Jenis Pemeriksaan, Tanggal, Hasil, dan Catatan (atau klik **Muat Data Fiktif**).
3. Klik **Simpan Rekam Medis**. Seluruh informasi sensitif otomatis dienkripsi dengan AES-256-GCM menggunakan subkunci turunan HKDF dari Master Key DPAPI Windows sebelum dikirim ke MySQL.
4. Tabel di bagian bawah menampilkan data yang telah didekripsi secara aman oleh aplikasi.
5. Anda dapat mengklik baris untuk mengubah data atau mengklik tombol **Hapus Data Terpilih** untuk menghapus rekaman dengan konfirmasi.

### F. Penggunaan Steganografi Citra Laboratorium
1. Buka menu **Steganografi Citra**.
2. Pada panel kiri, klik **Pilih Gambar PNG Asli** (format wajib PNG). Sistem akan menghitung kapasitas bit maksimal gambar.
3. Tulis pesan rahasia (misalnya ID sampel dan kode otentikasi) dan masukkan passphrase.
4. Klik **Sisipkan Pesan & Simpan Sebagai PNG Baru**. Pesan dipra-enkripsi dengan AES-256-GCM lalu disisipkan ke bit LSB piksel warna.
5. Pada panel kanan, pilih gambar PNG hasil steganografi, masukkan passphrase, lalu klik **Ekstrak & Dekripsi Pesan Rahasia**.

### G. Penggunaan Verifikasi Aset Digital Blockchain
1. Buka menu **Verifikasi Blockchain**.
2. Pada panel kiri, pilih berkas dokumen atau citra yang ingin didaftarkan, masukkan Kode Aset dan Keterangan, lalu klik **Hitung Hash SHA-256 & Buat Blok Baru di Blockchain**.
3. Sistem menghitung hash SHA-256 berkas secara streaming, mengambil hash blok sebelumnya, menyusun blok baru, dan menyimpannya ke tabel `blockchain_blocks` di MySQL.
4. Untuk verifikasi, pilih salah satu aset dari tabel buku besar, lalu klik **Verifikasi Aset Terpilih di Tabel**. Sistem akan menguji:
   - Keutuhan berkas terhadap hash yang dicatat pada blok.
   - Hubungan rantai previous_hash seluruh blok dari Genesis Block sampai akhir.
   - Menampilkan status [VALID], [INVALID], atau [CHAIN INVALID].
5. Untuk mendemonstrasikan deteksi kecurangan, klik **Uji File Lain (Uji Manipulasi)** untuk membuktikan bahwa berkas yang telah diubah akan langsung terdeteksi sebagai [INVALID].

---

## 11. CARA MENJALANKAN PENGUJIAN OTOMATIS (UNIT TESTS)

Pengujian mencakup 31 skenario uji unit otomatis untuk seluruh komponen kriptografi, hashing, biometrik, USB, steganografi, dan blockchain.

Jalankan perintah berikut:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Atau menggunakan pytest:

```powershell
pytest -v
```

Seluruh 31 pengujian dirancang independen, menguji skenario positif (berhasil), skenario negatif (penolakan kunci salah, deteksi manipulasi ciphertext, dan kegagalan integritas HMAC).

---

## 12. BATASAN KEAMANAN DAN CATATAN AKADEMIK

1. **USB Flashdisk Biasa vs Hardware Security Module (HSM):**
   USB flashdisk standar bukan merupakan hardware token berstandar FIPS 140-2 yang memiliki chip kriptografi anti-tamper. Mekanisme token acak 256-bit dan identifikasi nomor seri volume Windows API pada proyek ini merupakan pengamanan prototipe perangkat fisik untuk tingkat tugas perkuliahan, bukan perlindungan anti-kloning tingkat hardware bersertifikasi militer.

2. **Karakteristik AES-128-ECB:**
   Mode Electronic Codebook (ECB) digunakan khusus untuk memenuhi silabus demonstrasi tugas akhir Kriptografi (kombinasi Vigenere dan ECB). Mode ECB tidak menyembunyikan pola plaintext secara sempurna. Untuk sistem rekam medis produksi di rumah sakit, mode Galois/Counter Mode (AES-GCM) yang diterapkan pada Fitur Database adalah standar yang wajib digunakan.

3. **Karakteristik Simple Blockchain:**
   Implementasi blockchain pada aplikasi ini adalah buku besar rantai hash SHA-256 lokal yang disimpan di MySQL untuk membuktikan imutabilitas data dan deteksi manipulasi urutan catatan. Fitur ini bukan blockchain terdistribusi yang memiliki konsensus desentralisasi (Proof-of-Work atau Proof-of-Stake).

4. **Etika Penggunaan Steganografi Medis:**
   Steganografi LSB hanya boleh diujikan pada salinan citra non-diagnostik. Modifikasi bit LSB pada citra radiologi diagnostik primer (seperti DICOM mamografi atau CT-scan resolusi tinggi) tidak disarankan dalam etika rekayasa biomedis karena berpotensi memengaruhi interpretasi klinis dokter ahli.

