# pychatdemo
panduan instalasi pychat - whatsapp lite clone
# prerequisites
pastikan anda telah menginstal python 3.11 atau versi yang lebih baru dan pip (python package manager).
# langkah-langkah instalasi
clone atau download project
jika menggunakan git: git clone <repository-url> lalu cd pychat
atau download dan ekstrak file zip, kemudian masuk ke direktori project
# buat virtual environment (rekomendasi)
windows: python -m venv venv lalu venv\scripts\activate
macos/linux: python3 -m venv venv lalu source venv/bin/activate
# install dependencies
jalankan perintah: pip install -r requirements.txt
# setup database
aplikasi akan secara otomatis membuat database sqlite saat pertama kali dijalankan.
file database pychat.db akan dibuat di direktori project.
# jalankan aplikasi
jalankan server dengan perintah: python app.py
aplikasi akan berjalan di http://localhost:5000
# akses aplikasi
buka browser dan kunjungi http://localhost:5000.
register akun baru atau login dengan akun yang sudah dibuat.
# struktur project
setelah instalasi, struktur project akan terlihat seperti ini:

<img width="679" height="623" alt="Screenshot (408)" src="https://github.com/user-attachments/assets/5bce17ff-b526-4319-baf5-48e09bd69ecc" />

# catatan penting
pastikan port 5000 tidak digunakan oleh aplikasi lain
folder uploads akan dibuat otomatis untuk menyimpan file yang diupload
aplikasi menggunakan sqlite sebagai database default (untuk development)
untuk production, disarankan menggunakan postgresql dengan mengubah konfigurasi database di app.py
