-- Lab 6: виконується автоматично ОДИН раз при першому старті Primary (порожній volume).
-- Окремий користувач, під яким Replica підключається до Primary і читає WAL.
-- Якщо volume вже існував (дані з Lab 1-5) — виконайте цей файл вручну (див. README, розділ Lab 6).
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
    CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replicator';
  END IF;
END $$;
