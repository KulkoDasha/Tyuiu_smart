package main

import "time"

type Base struct {
	CreatedAt time.Time `db:"created_at"`
	UpdatedAt time.Time `db:"updated_at"`
}

type EventApplication struct {
	ID                     int64     `db:"id"`
	TgID                   int64     `db:"tg_id"`
	FullName               string    `db:"full_name"`
	Username               string    `db:"username"`
	EventDirection         string    `db:"event_direction"`
	EventName              string    `db:"event_name"`
	DateOfEvent            time.Time `db:"date_of_event"`
	EventPlace             string    `db:"event_place"`
	EventRole              string    `db:"event_role"`
	EventApplicationStatus string    `db:"event_application_status"`
	AmountTiukoins         float64   `db:"amount_tiukoins"`
	Moderator              string    `db:"moderator"`
	Base                   `db:",embedded"`
}

type IssuanceOfRewards struct {
	ID                int64     `db:"id"`
	TgID              int64     `db:"tg_id"`
	UserName          string    `db:"username"`
	RewardID          *int64    `db:"reward_id"`
	NameOfReward      string    `db:"name_of_reward"`
	Price             int       `db:"price"`
	OrderDate         time.Time `db:"order_date"`
	Status            string    `db:"status"`
	ModeratorUsername string    `db:"moderator_username"`
	Base              `db:",embedded"`
}

type User struct {
	ID                int       `db:"id"`
	TgID              int       `db:"tg_id"`
	FullName          string    `db:"full_name"`
	UserName          string    `db:"username"`
	Tiukoins          float64   `db:"tiukoins"`
	ApprovalDate      time.Time `db:"approval_date"`
	ModeratorUsername string    `db:"moderator_username"`
	Base              `db:",embedded"`
}

type UserExcelTable struct {
	User
	StructuralUnit string
	Course         string
	Group          string
}

type CatalogOfReward struct {
	ID           int    `db:"id"`
	NameOfReward string `db:"name_of_reward"`
	Count        int    `db:"count"`
	Price        int    `db:"price"`
	Note         string `db:"note"`
	LinkOnPhoto  string `db:"link_on_photo"`
	Base         `db:",embedded"`
}
