-- Создание таблицы users
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    tiukoins DOUBLE PRECISION NOT NULL DEFAULT 0,
    approval_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    moderator_username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы roles
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    role VARCHAR(255) UNIQUE NOT NULL,
    base_value_tiukoins DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы event_applications
CREATE TABLE IF NOT EXISTS event_applications (
    id BIGSERIAL PRIMARY KEY,
    tg_id BIGINT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    event_direction VARCHAR(255) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    date_of_event TIMESTAMP NOT NULL,
    event_place VARCHAR(255) NOT NULL,
    event_role VARCHAR(255) NOT NULL,
    event_application_status VARCHAR(255) NOT NULL,
    amount_tiukoins DOUBLE PRECISION NOT NULL DEFAULT 0,
    moderator VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_applications_user FOREIGN KEY (tg_id) 
        REFERENCES users(tg_id) ON DELETE CASCADE
);

-- Создание индексов для event_applications
CREATE INDEX idx_event_applications_tg_id ON event_applications(tg_id);
CREATE INDEX idx_event_applications_event_name ON event_applications(event_name);
CREATE INDEX idx_event_applications_status ON event_applications(event_application_status);

-- Создание таблицы catalog_of_reward
CREATE TABLE IF NOT EXISTS catalog_of_reward (
    id BIGSERIAL PRIMARY KEY,
    name_of_reward VARCHAR(255) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    price INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL,
    link_on_photo VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создание индекса для catalog_of_reward
CREATE INDEX idx_catalog_name ON catalog_of_reward(name_of_reward);

-- Создание таблицы issuance_of_rewards
CREATE TABLE IF NOT EXISTS issuance_of_rewards (
    id BIGSERIAL PRIMARY KEY,
    tg_id BIGINT NOT NULL,
    username VARCHAR(255) NOT NULL,
    reward_id BIGINT,
    name_of_reward VARCHAR(255) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(255) NOT NULL,
    moderator_username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_issuance_reward FOREIGN KEY (reward_id) 
        REFERENCES catalog_of_reward(id) ON DELETE SET NULL
);

-- Создание индексов для issuance_of_rewards
CREATE INDEX idx_issuance_tg_id ON issuance_of_rewards(tg_id);
CREATE INDEX idx_issuance_reward_id ON issuance_of_rewards(reward_id);
CREATE INDEX idx_issuance_status ON issuance_of_rewards(status);

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггеров для обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_applications_updated_at BEFORE UPDATE ON event_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_catalog_updated_at BEFORE UPDATE ON catalog_of_reward
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_issuance_updated_at BEFORE UPDATE ON issuance_of_rewards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
