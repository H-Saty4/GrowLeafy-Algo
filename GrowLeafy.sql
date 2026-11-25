CREATE TABLE kategori(
id_kategori INT PRIMARY KEY,
nama_kategori VARCHAR(50) NOT NULL
);

CREATE TABLE tanaman(
id_tanaman INT PRIMARY KEY,
nama_tanaman VARCHAR(100) NOT NULL,
deskripsi TEXT,
harga int not null,
stok int not null,
gambar_tanaman varchar(250) not null,
id_kategori int,
foreign key (id_kategori) references kategori(id_kategori)
);

CREATE TABLE users (
    id_user SERIAL PRIMARY KEY,
    nama_lengkap VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    passwords TEXT NOT NULL,
    roles VARCHAR(10) NOT NULL
        CHECK (roles IN ('pembeli', 'kasir', 'owner'))
);

create table metode_pembayaran(
id_metode_pembayaran serial primary key,
nama_metode varchar(50) not null,
nomor_rekening varchar(50) not null
);

create table pesanan(
id_pesanan varchar(20) primary key,
nama_pembeli varchar(100) not null,
nomor_hp varchar(15) not null,
alamat_pengiriman text,
total_bayar int not null,
status_pesanan varchar(20) not null,
tanggal_pesanan date not null,
id_metode_pembayaran int,
foreign key (id_metode_pembayaran) references metode_pembayaran(id_metode_pembayaran)
);

create table detail_pesanan(
id_detail_pesanan int primary key,
jumlah int not null,
subtotal int not null,
id_pesanan varchar(20),
foreign key (id_pesanan) references pesanan(id_pesanan),
id_tanaman int,
foreign key (id_tanaman) references tanaman(id_tanaman)
);