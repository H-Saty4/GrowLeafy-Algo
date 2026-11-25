import psycopg2
import pandas as pd
from datetime import date
import os

def connectDB():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="2708",
            dbname="growleafy"
        )
        cur = conn.cursor()
        return conn, cur

    except Exception as error:
        print("Koneksi database gagal:", error)
        return None, None


def tutupKoneksi(conn, cur):
    if cur:
        cur.close()
    if conn:
        conn.close()


def formatRupiah(nilai):
    return "Rp" + format(int(nilai), ",").replace(",", ".")


def jeda():
    input("\nTekan Enter untuk melanjutkan...")


def bersihkanLayar():
    os.system("cls" if os.name == "nt" else "clear")


def ambilData(query, params=None, kolom=None):
    conn, cur = connectDB()
    if not conn:
        return pd.DataFrame()

    try:
        cur.execute(query, params or ())
        data = cur.fetchall()
        if kolom is None:
            kolom = [desc[0] for desc in cur.description]
        return pd.DataFrame(data, columns=kolom)
    except Exception as error:
        print("Gagal mengambil data:", error)
        return pd.DataFrame()
    finally:
        tutupKoneksi(conn, cur)

def login():
    print("\n========== LOGIN GROWLEAFY ==========")
    username = input("Username : ").strip()
    password = input("Password : ").strip()

    conn, cur = connectDB()
    if not conn:
        return None

    try:
        cur.execute("""
            SELECT id_user, nama_lengkap, username, roles
            FROM users
            WHERE username = %s AND passwords = %s
        """, (username, password))

        user = cur.fetchone()

        if user:
            print(f"\nLogin berhasil. Selamat datang, {user[1]}!")
            return {
                "id_user": user[0],
                "nama": user[1],
                "username": user[2],
                "role": user[3]
            }

        print("Username atau password salah.")
        return None

    except Exception as error:
        print("Login gagal:", error)
        return None
    finally:
        tutupKoneksi(conn, cur)



def getAllTanaman():
    return ambilData("""
        SELECT t.id_tanaman, t.nama_tanaman, k.nama_kategori,
               t.deskripsi, t.harga, t.stok
        FROM tanaman t
        JOIN kategori k ON t.id_kategori = k.id_kategori
        ORDER BY t.id_tanaman
    """, kolom=[
        "ID", "Nama Tanaman", "Kategori",
        "Deskripsi", "Harga", "Stok"
    ])

def tampilkanKatalog():
    data = getAllTanaman()
    if data.empty:
        print("Belum ada data tanaman.")
        return

    tampilan = data.copy()
    tampilan["Harga"] = tampilan["Harga"].apply(formatRupiah)
    print("\n================ KATALOG GROWLEAFY ================")
    print(tampilan.to_string(index=False))











def daftarPesanan():
    data = ambilData("""
        SELECT id_pesanan, nama_pembeli, nomor_hp,
               tanggal_pesanan, total_bayar, status_pesanan
        FROM pesanan
        ORDER BY id_pesanan DESC
    """, kolom=[
        "ID Pesanan", "Pembeli", "Nomor HP",
        "Tanggal", "Total Bayar", "Status"
    ])

    if data.empty:
        print("Belum ada pesanan.")
        return

    tampilan = data.copy()
    tampilan["Total Bayar"] = tampilan["Total Bayar"].apply(formatRupiah)
    print("\n================ DAFTAR PESANAN ================")
    print(tampilan.to_string(index=False))


def detailPesanan(id_pesanan):
    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            SELECT p.id_pesanan, p.nama_pembeli, p.nomor_hp,
                   p.alamat_pengiriman, p.total_bayar,
                   p.status_pesanan, p.tanggal_pesanan,
                   m.nama_metode, m.nomor_rekening
            FROM pesanan p
            JOIN metode_pembayaran m
              ON p.id_metode_pembayaran = m.id_metode_pembayaran
            WHERE p.id_pesanan = %s
        """, (id_pesanan,))
        pesanan = cur.fetchone()

        if not pesanan:
            print("Pesanan tidak ditemukan.")
            return

        cur.execute("""
            SELECT t.nama_tanaman, d.jumlah, t.harga, d.subtotal
            FROM detail_pesanan d
            JOIN tanaman t ON d.id_tanaman = t.id_tanaman
            WHERE d.id_pesanan = %s
        """, (id_pesanan,))
        detail = cur.fetchall()

        print("\n================ DETAIL PESANAN ================")
        print("ID Pesanan       :", pesanan[0])
        print("Nama Pembeli     :", pesanan[1])
        print("Nomor HP         :", pesanan[2])
        print("Alamat           :", pesanan[3])
        print("Tanggal          :", pesanan[6])
        print("Metode Pembayaran:", pesanan[7])
        print("Nomor Rekening   :", pesanan[8])
        print("Status           :", pesanan[5])
        print("\nRincian Produk:")
        for nama, jumlah, harga, subtotal in detail:
            print(
                f"- {nama} | {jumlah} x {formatRupiah(harga)}"
                f" = {formatRupiah(subtotal)}"
            )
        print("\nTotal:", formatRupiah(pesanan[4]))
    finally:
        tutupKoneksi(conn, cur)


def konfirmasiPembayaran():
    daftarPesanan()
    try:
        id_pesanan = int(input("\nID pesanan yang diverifikasi: "))
    except ValueError:
        print("ID pesanan harus berupa angka.")
        return

    detailPesanan(id_pesanan)
    print("\nPastikan pembayaran sudah diterima melalui rekening toko.")
    konfirmasi = input("Pembayaran valid? (y/n): ").strip().lower()

    conn, cur = connectDB()
    if not conn:
        return

    try:
        if konfirmasi == "y":
            cur.execute("""
                UPDATE pesanan
                SET status_pesanan = 'Diproses'
                WHERE id_pesanan = %s
                  AND status_pesanan = 'Menunggu Verifikasi'
            """, (id_pesanan,))
        elif konfirmasi == "n":
            cur.execute("""
                UPDATE pesanan
                SET status_pesanan = 'Ditolak'
                WHERE id_pesanan = %s
                  AND status_pesanan = 'Menunggu Verifikasi'
            """, (id_pesanan,))
        else:
            print("Pilihan tidak valid.")
            return

        jumlah = cur.rowcount
        conn.commit()

        if jumlah:
            print("Status pembayaran berhasil diperbarui.")
        else:
            print("Pesanan tidak ditemukan atau sudah diverifikasi.")
    except Exception as error:
        conn.rollback()
        print("Gagal memperbarui pembayaran:", error)
    finally:
        tutupKoneksi(conn, cur)


def updateStatusPesanan():
    daftarPesanan()
    try:
        id_pesanan = int(input("\nID pesanan: "))
    except ValueError:
        print("ID pesanan harus berupa angka.")
        return

    detailPesanan(id_pesanan)
    print("\n[1] Diproses")
    print("[2] Dikirim")
    print("[3] Selesai")
    pilihan = input("Pilih status baru: ").strip()

    match pilihan:
        case "1":
            status_baru = "Diproses"
        case "2":
            status_baru = "Dikirim"
        case "3":
            status_baru = "Selesai"
        case _:
            print("Pilihan status tidak valid.")
            return
    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            UPDATE pesanan
            SET status_pesanan = %s
            WHERE id_pesanan = %s
              AND status_pesanan <> 'Ditolak'
        """, (status_baru, id_pesanan))
        jumlah = cur.rowcount
        conn.commit()

        if jumlah:
            print(f"Status pesanan berhasil diubah menjadi {status_baru}.")
        else:
            print("Pesanan tidak ditemukan atau berstatus Ditolak.")
    except Exception as error:
        conn.rollback()
        print("Gagal mengubah status:", error)
    finally:
        tutupKoneksi(conn, cur)


def cetakNota():
    try:
        id_pesanan = int(input("\nMasukkan ID pesanan: "))
    except ValueError:
        print("ID pesanan harus berupa angka.")
        return

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            SELECT p.id_pesanan, p.nama_pembeli, p.nomor_hp,
                   p.alamat_pengiriman, p.total_bayar,
                   p.status_pesanan, p.tanggal_pesanan,
                   m.nama_metode
            FROM pesanan p
            JOIN metode_pembayaran m
              ON p.id_metode_pembayaran = m.id_metode_pembayaran
            WHERE p.id_pesanan = %s
        """, (id_pesanan,))
        p = cur.fetchone()

        if not p:
            print("Pesanan tidak ditemukan.")
            return

        cur.execute("""
            SELECT t.nama_tanaman, d.jumlah, t.harga, d.subtotal
            FROM detail_pesanan d
            JOIN tanaman t ON d.id_tanaman = t.id_tanaman
            WHERE d.id_pesanan = %s
        """, (id_pesanan,))
        items = cur.fetchall()

        nama_file = f"Nota_GrowLeafy_{id_pesanan}.txt"
        with open(nama_file, "w", encoding="utf-8") as file:
            file.write("============== GROWLEAFY ==============\n")
            file.write("             NOTA PESANAN              \n")
            file.write("---------------------------------------\n")
            file.write(f"ID Pesanan : {p[0]}\n")
            file.write(f"Tanggal    : {p[6]}\n")
            file.write(f"Penerima   : {p[1]}\n")
            file.write(f"No. HP     : {p[2]}\n")
            file.write(f"Alamat     : {p[3]}\n")
            file.write(f"Pembayaran : {p[7]}\n")
            file.write(f"Status     : {p[5]}\n")
            file.write("---------------------------------------\n")
            for nama, jumlah, harga, subtotal in items:
                file.write(
                    f"{nama}\n{jumlah} x {formatRupiah(harga)}"
                    f" = {formatRupiah(subtotal)}\n"
                )
            file.write("---------------------------------------\n")
            file.write(f"TOTAL: {formatRupiah(p[4])}\n")
            file.write("Terima kasih telah berbelanja!\n")

        print(f"Nota berhasil dibuat: {nama_file}")
    except Exception as error:
        print("Gagal mencetak nota:", error)
    finally:
        tutupKoneksi(conn, cur)


def cetakLabelPengiriman():
    try:
        id_pesanan = int(input("\nMasukkan ID pesanan: "))
    except ValueError:
        print("ID pesanan harus berupa angka.")
        return

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            SELECT id_pesanan, nama_pembeli, nomor_hp, alamat_pengiriman
            FROM pesanan
            WHERE id_pesanan = %s
        """, (id_pesanan,))
        p = cur.fetchone()

        if not p:
            print("Pesanan tidak ditemukan.")
            return

        nama_file = f"Label_GrowLeafy_{id_pesanan}.txt"
        with open(nama_file, "w", encoding="utf-8") as file:
            file.write("========== LABEL PENGIRIMAN ==========\n")
            file.write("             GROWLEAFY                 \n")
            file.write("---------------------------------------\n")
            file.write(f"ID PESANAN : {p[0]}\n")
            file.write(f"PENERIMA   : {p[1]}\n")
            file.write(f"NO. HP     : {p[2]}\n")
            file.write(f"ALAMAT     : {p[3]}\n")
            file.write("---------------------------------------\n")
            file.write("Mohon jaga tanaman agar tetap aman.\n")

        print(f"Label pengiriman berhasil dibuat: {nama_file}")
    except Exception as error:
        print("Gagal membuat label:", error)
    finally:
        tutupKoneksi(conn, cur)

def getAllKategori():
    return ambilData("""
        SELECT id_kategori, nama_kategori
        FROM kategori
        ORDER BY id_kategori
    """, kolom=["ID Kategori", "Nama Kategori"])

def tampilkanKategori():
    data = getAllKategori()
    print("\n========== DATA KATEGORI ==========")
    if data.empty:
        print("Belum ada kategori.")
    else:
        print(data.to_string(index=False))


def tambahTanaman():
    print("\n========== TAMBAH TANAMAN ==========")
    nama = input("Nama tanaman : ").strip()
    deskripsi = input("Deskripsi    : ").strip()

    try:
        harga = int(input("Harga        : "))
        stok = int(input("Stok         : "))
        if harga < 0 or stok < 0:
            print("Harga dan stok tidak boleh negatif.")
            return
    except ValueError:
        print("Harga dan stok harus berupa angka.")
        return

    tampilkanKategori()
    try:
        id_kategori = int(input("ID kategori  : "))
    except ValueError:
        print("ID kategori harus berupa angka.")
        return

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            INSERT INTO tanaman
            (nama_tanaman, deskripsi, harga, stok, id_kategori)
            VALUES (%s, %s, %s, %s, %s)
        """, (nama, deskripsi, harga, stok, id_kategori))
        conn.commit()
        print("Tanaman berhasil ditambahkan.")
    except Exception as error:
        conn.rollback()
        print("Gagal menambahkan tanaman:", error)
    finally:
        tutupKoneksi(conn, cur)


def updateTanaman():
    tampilkanKatalog()
    try:
        id_tanaman = int(input("\nID tanaman yang diubah: "))
    except ValueError:
        print("ID harus berupa angka.")
        return

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("""
            SELECT nama_tanaman, deskripsi, harga, stok, id_kategori
            FROM tanaman
            WHERE id_tanaman = %s
        """, (id_tanaman,))
        lama = cur.fetchone()

        if not lama:
            print("Tanaman tidak ditemukan.")
            return

        print("Kosongkan input jika data tidak ingin diubah.")
        nama = input(f"Nama [{lama[0]}]: ").strip() or lama[0]
        deskripsi = input(f"Deskripsi [{lama[1]}]: ").strip() or lama[1]

        harga_input = input(f"Harga [{lama[2]}]: ").strip()
        stok_input = input(f"Stok [{lama[3]}]: ").strip()

        harga = int(harga_input) if harga_input else lama[2]
        stok = int(stok_input) if stok_input else lama[3]

        tampilkanKategori()
        kategori_input = input(f"ID kategori [{lama[4]}]: ").strip()
        id_kategori = int(kategori_input) if kategori_input else lama[4]

        if harga < 0 or stok < 0:
            print("Harga dan stok tidak boleh negatif.")
            return

        cur.execute("""
            UPDATE tanaman
            SET nama_tanaman = %s, deskripsi = %s,
                harga = %s, stok = %s, id_kategori = %s
            WHERE id_tanaman = %s
        """, (nama, deskripsi, harga, stok, id_kategori, id_tanaman))
        conn.commit()
        print("Data tanaman berhasil diperbarui.")
    except ValueError:
        conn.rollback()
        print("Harga, stok, dan ID kategori harus berupa angka.")
    except Exception as error:
        conn.rollback()
        print("Gagal memperbarui tanaman:", error)
    finally:
        tutupKoneksi(conn, cur)


def hapusTanaman():
    tampilkanKatalog()
    try:
        id_tanaman = int(input("\nID tanaman yang dihapus: "))
    except ValueError:
        print("ID harus berupa angka.")
        return

    konfirmasi = input("Yakin ingin menghapus tanaman? (y/n): ").lower()
    if konfirmasi != "y":
        print("Penghapusan dibatalkan.")
        return

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute("DELETE FROM tanaman WHERE id_tanaman = %s", (id_tanaman,))
        jumlah = cur.rowcount
        conn.commit()
        if jumlah:
            print("Tanaman berhasil dihapus.")
        else:
            print("Tanaman tidak ditemukan.")
    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()
        print("Tanaman tidak dapat dihapus karena sudah tercatat dalam pesanan.")
    except Exception as error:
        conn.rollback()
        print("Gagal menghapus tanaman:", error)
    finally:
        tutupKoneksi(conn, cur)


def analisisStok():
    data = getAllTanaman()
    if data.empty:
        print("Tidak ada data tanaman.")
        return

    data["Nilai Persediaan"] = data["Harga"] * data["Stok"]
    data["Keterangan Stok"] = data["Stok"].apply(
        lambda stok: "Stok Menipis" if stok <= 5 else "Tersedia"
    )

    tampilan = data[[
        "ID", "Nama Tanaman", "Stok",
        "Harga", "Nilai Persediaan", "Keterangan Stok"
    ]].copy()
    tampilan["Harga"] = tampilan["Harga"].apply(formatRupiah)
    tampilan["Nilai Persediaan"] = tampilan["Nilai Persediaan"].apply(formatRupiah)

    print("\n========== ANALISIS PERSEDIAAN ==========")
    print(tampilan.to_string(index=False))
    print("\nTotal nilai persediaan:",
          formatRupiah(data["Nilai Persediaan"].sum()))


def laporanPenjualan():
    print("\n========== LAPORAN PENJUALAN ==========")
    print("[1] Harian")
    print("[2] Mingguan")
    print("[3] Bulanan")
    pilihan = input("Pilih periode: ").strip()

    match pilihan:
        case "1":
            filter_tanggal = "tanggal_pesanan = CURRENT_DATE"
            judul = "HARIAN"
        case "2":
            filter_tanggal = (
                "tanggal_pesanan >= CURRENT_DATE - INTERVAL '6 days' "
                "AND tanggal_pesanan <= CURRENT_DATE"
            )
            judul = "7 HARI TERAKHIR"
        case "3":
            filter_tanggal = (
                "DATE_TRUNC('month', tanggal_pesanan) = "
                "DATE_TRUNC('month', CURRENT_DATE)"
            )
            judul = "BULANAN"
        case _:
            print("Pilihan tidak valid.")
            return

    query = f"""
        SELECT tanggal_pesanan, id_pesanan, nama_pembeli, total_bayar
        FROM pesanan
        WHERE status_pesanan = 'Selesai'
          AND {filter_tanggal}
        ORDER BY tanggal_pesanan
    """

    conn, cur = connectDB()
    if not conn:
        return

    try:
        cur.execute(query)
        data_laporan = cur.fetchall()
        jumlah_pesanan = len(data_laporan)
        total_penjualan = sum(row[3] for row in data_laporan) if data_laporan else 0

        cur.execute("""
            SELECT t.nama_tanaman, COALESCE(SUM(d.jumlah), 0) AS total_terjual
            FROM tanaman t
            LEFT JOIN detail_pesanan d ON t.id_tanaman = d.id_tanaman
            LEFT JOIN pesanan p ON d.id_pesanan = p.id_pesanan
                AND p.status_pesanan = 'Selesai'
            GROUP BY t.id_tanaman, t.nama_tanaman
            ORDER BY total_terjual DESC, t.nama_tanaman
        """)
        data_produk = cur.fetchall()

        print(f"\n========== LAPORAN {judul} ==========")
        print("Jumlah pesanan selesai :", jumlah_pesanan)
        print("Total penjualan        :", formatRupiah(total_penjualan))

        if data_produk:
            terlaris = data_produk[0]
            kurang_laris = data_produk[-1]
            print("Produk terlaris        :", terlaris[0], f"({terlaris[1]} terjual)")
            print("Produk kurang laris    :", kurang_laris[0], f"({kurang_laris[1]} terjual)")
        else:
            print("Produk terlaris        : Belum ada data")
            print("Produk kurang laris    : Belum ada data")

        baris_csv = []
        baris_csv.append(["LAPORAN HASIL PENJUALAN", judul])
        baris_csv.append(["Jumlah pesanan selesai", jumlah_pesanan])
        baris_csv.append(["Total penjualan", total_penjualan])
        baris_csv.append([])
        baris_csv.append(["RINCIAN PENJUALAN"])
        baris_csv.append(["Tanggal", "ID Pesanan", "Nama Pembeli", "Total Bayar"])
        baris_csv.extend(data_laporan)
        baris_csv.append([])
        baris_csv.append(["PRODUK TERLARIS"])
        baris_csv.append(["Nama Tanaman", "Jumlah Terjual"])
        baris_csv.extend(data_produk)
        baris_csv.append([])
        baris_csv.append(["PRODUK KURANG LARIS"])
        baris_csv.append(["Nama Tanaman", "Jumlah Terjual"])
        baris_csv.extend(sorted(data_produk, key=lambda x: x[1]))

        nama_file = f"Laporan_GrowLeafy_{pilihan}_{date.today()}.csv"
        lokasi_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), nama_file)
        pd.DataFrame(baris_csv).to_csv(
            lokasi_file, index=False, header=False, encoding="utf-8-sig"
        )
        print("\nLaporan lengkap berhasil disimpan ke CSV:")
        print(nama_file)

    except Exception as error:
        print("Gagal membuat laporan:", error)
    finally:
        tutupKoneksi(conn, cur)

def produkTerlaris():
    data = ambilData("""
        SELECT t.nama_tanaman, SUM(d.jumlah) AS total_terjual
        FROM detail_pesanan d
        JOIN pesanan p ON d.id_pesanan = p.id_pesanan
        JOIN tanaman t ON d.id_tanaman = t.id_tanaman
        WHERE p.status_pesanan = 'Selesai'
        GROUP BY t.id_tanaman, t.nama_tanaman
        ORDER BY total_terjual DESC
    """, kolom=["Nama Tanaman", "Jumlah Terjual"])

    print("\n========== PRODUK TERLARIS ==========")
    if data.empty:
        print("Belum ada transaksi selesai.")
    else:
        print(data.to_string(index=False))




def menuKasir(user):
    while True:
        print(f"\n========== DASHBOARD KASIR: {user['nama']} ==========")
        print("[1] Lihat Pesanan Masuk")
        print("[2] Detail Pesanan")
        print("[3] Verifikasi Pembayaran")
        print("[4] Update Status Pesanan")
        print("[5] Cetak Nota")
        print("[6] Cetak Label Pengiriman")
        print("[0] Logout")

        pilihan = input("Masukkan pilihan: ").strip()

        match pilihan:
            case "1":
                daftarPesanan()
            case "2":
                try:
                    id_pesanan = int(input("Masukkan ID pesanan: "))
                    detailPesanan(id_pesanan)
                except ValueError:
                    print("ID harus berupa angka.")
            case "3":
                konfirmasiPembayaran()
            case "4":
                updateStatusPesanan()
            case "5":
                cetakNota()
            case "6":
                cetakLabelPengiriman()
            case "0":
                break
            case _:
                print("Pilihan tidak valid.")

        if pilihan != "0":
            jeda()


def menuOwner(user):
    while True:
        print(f"\n========== DASHBOARD OWNER: {user['nama']} ==========")
        print("[1] Lihat Data Tanaman")
        print("[2] Tambah Tanaman")
        print("[3] Update Data Tanaman / Stok")
        print("[4] Hapus Tanaman")
        print("[5] Lihat Kategori")
        print("[6] Analisis Stok")
        print("[7] Laporan Penjualan")
        print("[8] Lihat Semua Pesanan")
        print("[0] Logout")

        pilihan = input("Masukkan pilihan: ").strip()

        match pilihan:
            case "1":
                tampilkanKatalog()
            case "2":
                tambahTanaman()
            case "3":
                updateTanaman()
            case "4":
                hapusTanaman()
            case "5":
                tampilkanKategori()
            case "6":
                analisisStok()
            case "7":
                laporanPenjualan()
            case "8":
                daftarPesanan()
            case "0":
                break
            case _:
                print("Pilihan tidak valid.")

        if pilihan != "0":
            jeda()


def menuUtama():
    while True:
        print("\n========================================")
        print("          GROWLEAFY PLANT STORE")
        print(" Sistem Penjualan dan Perawatan Tanaman")
        print("========================================")
        print("[1] Login")
        print("[2] Keluar")

        pilihan = input("Masukkan pilihan: ").strip()

        match pilihan:
            case "1":
                user = login()
                if user:
                    role = user["role"].lower()
                    match role:
                        case "kasir":
                            menuKasir(user)
                        case "owner":
                            menuOwner(user)
                        case _:
                            print("Role pengguna tidak dikenali.")
            case "2":
                print("Terima kasih telah menggunakan GrowLeafy.")
                break
            case _:
                print("Pilihan tidak valid.")

        if pilihan != "2":
            jeda()

if __name__ == "__main__":
    menuUtama()
