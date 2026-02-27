CREATE TABLE event_application (
    id                       SERIAL PRIMARY KEY,
    tg_id                  INTEGER NOT NULL,
    full_name               VARCHAR(255) NOT NULL,
    event_direction         VARCHAR(100) NOT NULL,
    event_name             VARCHAR(255) NOT NULL,
    date_of_event          TIMESTAMP WITH TIME ZONE NOT NULL,
    event_place            VARCHAR(255) NOT NULL,
    event_role             VARCHAR(100) NOT NULL,
    event_application_status VARCHAR(50) NOT NULL,
    amount_tiukoins        REAL NOT NULL,
    moderator              VARCHAR(100) NOT NULL
);
