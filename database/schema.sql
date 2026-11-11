-- Skema Database MediCipher (Medical Data Encryption and Security System)
-- Target Database: MySQL 8.0+ / MariaDB 10.4+
-- Karakteristik: InnoDB, UTF-8 (utf8mb4), Foreign Keys, Parameterized Data Storage

CREATE DATABASE IF NOT EXISTS `medicipher_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `medicipher_db`;

-- 1. Tabel Pengguna (Users)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(64) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabel Template Wajah Terenkripsi (Face Templates)
-- Embedding wajah 512 dimensi disimpan dalam bentuk terenkripsi AES-256-GCM
CREATE TABLE IF NOT EXISTS `face_templates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `encrypted_embedding` LONGBLOB NOT NULL,
    `nonce` VARBINARY(16) NOT NULL,
    `tag` VARBINARY(16) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_face_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabel Perangkat USB Dongle (Dongle Devices)
-- Hanya menyimpan serial volume dan hash SHA-256 token rahasia
CREATE TABLE IF NOT EXISTS `dongle_devices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `volume_serial` VARCHAR(64) NOT NULL,
    `token_hash` VARCHAR(64) NOT NULL,
    `registered_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_dongle_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Tabel Arsip Medis Terenkripsi (Medical Records)
-- Seluruh informasi medis sensitif dienkripsi menggunakan AES-256-GCM
CREATE TABLE IF NOT EXISTS `medical_records` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `record_code` VARCHAR(64) NOT NULL UNIQUE,
    `patient_code_enc` LONGBLOB NOT NULL,
    `patient_name_enc` LONGBLOB NOT NULL,
    `exam_type_enc` LONGBLOB NOT NULL,
    `exam_date` DATE NOT NULL,
    `result_enc` LONGBLOB NOT NULL,
    `notes_enc` LONGBLOB NOT NULL,
    `nonce` VARBINARY(16) NOT NULL,
    `tag` VARBINARY(16) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_record_code` (`record_code`),
    INDEX `idx_exam_date` (`exam_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Tabel Aset Dokumen & Gambar Medis (Medical Assets)
CREATE TABLE IF NOT EXISTS `medical_assets` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `asset_code` VARCHAR(64) NOT NULL UNIQUE,
    `file_name` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `file_hash` VARCHAR(64) NOT NULL,
    `description` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_asset_code` (`asset_code`),
    INDEX `idx_file_hash` (`file_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Tabel Rantai Blok Verifikasi (Blockchain Blocks)
-- Simple Blockchain berbasis SHA-256 Hash Chain
CREATE TABLE IF NOT EXISTS `blockchain_blocks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `block_index` INT NOT NULL,
    `asset_id` INT NULL,
    `block_data` LONGTEXT NOT NULL,
    `previous_hash` VARCHAR(64) NOT NULL,
    `current_hash` VARCHAR(64) NOT NULL,
    `timestamp` DATETIME NOT NULL,
    INDEX `idx_block_index` (`block_index`),
    CONSTRAINT `fk_block_asset` FOREIGN KEY (`asset_id`) REFERENCES `medical_assets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Tabel Log Audit Aktivitas & Keamanan (Audit Logs)
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `activity` VARCHAR(255) NOT NULL,
    `status` VARCHAR(64) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_log_activity` (`activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

