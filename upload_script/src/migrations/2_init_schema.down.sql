-- Удаление триггеров
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_roles_updated_at ON roles;
DROP TRIGGER IF EXISTS update_event_applications_updated_at ON event_applications;
DROP TRIGGER IF EXISTS update_catalog_updated_at ON catalog_of_reward;
DROP TRIGGER IF EXISTS update_issuance_updated_at ON issuance_of_rewards;

-- Удаление функции
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Удаление таблиц в обратном порядке (с учетом зависимостей)
DROP TABLE IF EXISTS issuance_of_rewards;
DROP TABLE IF EXISTS catalog_of_reward;
DROP TABLE IF EXISTS event_applications;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS users;
