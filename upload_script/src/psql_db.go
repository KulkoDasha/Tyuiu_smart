package main

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
)

type Database struct {
	*pgx.Conn
}

func ConnectDB(ctx context.Context, url string) (*Database, error) {
	conn, err := pgx.Connect(ctx, url)
	if err != nil {
		return nil, fmt.Errorf("Unable to connect to database: %w", err)
	}

	return &Database{conn}, nil
}

func (db *Database) ListEventApplication(ctx context.Context) ([]EventApplication, error) {
	rows, err := db.Query(ctx, `select * from "event_applications"`)
	if err != nil {
		return nil, fmt.Errorf("error selecting from event application: %w", err)
	}

	apps, err := pgx.CollectRows(rows, pgx.RowToStructByName[EventApplication])
	if err != nil {
		return nil, fmt.Errorf("error scanning rows in get event applications: %w", err)
	}

	return apps, nil
}

func (db *Database) ListUser(ctx context.Context) ([]User, error) {
	rows, err := db.Query(ctx, `select * from "users"`)
	if err != nil {
		return nil, fmt.Errorf("error selecting from user: %w", err)
	}

	users, err := pgx.CollectRows(rows, pgx.RowToStructByName[User])
	if err != nil {
		return nil, fmt.Errorf("error scanning rows in get users: %w", err)
	}

	return users, nil
}

func (db *Database) ListIssuanceOfRewards(ctx context.Context) ([]IssuanceOfRewards, error) {
	rows, err := db.Query(ctx, `select * from "issuance_of_rewards"`)
	if err != nil {
		return nil, fmt.Errorf("error selecting from issuance_of_rewards: %w", err)
	}

	issuance, err := pgx.CollectRows(rows, pgx.RowToStructByName[IssuanceOfRewards])
	if err != nil {
		return nil, fmt.Errorf("error scanning rows in get issuance_of_rewards: %w", err)
	}

	return issuance, nil

}

func (db *Database) ListCatalogOfReward(ctx context.Context) ([]CatalogOfReward, error) {
	rows, err := db.Query(ctx, `select * from "catalog_of_reward"`)
	if err != nil {
		return nil, fmt.Errorf("error selecting from user: %w", err)
	}

	catalog, err := pgx.CollectRows(rows, pgx.RowToStructByName[CatalogOfReward])
	if err != nil {
		return nil, fmt.Errorf("error scanning rows in get users: %w", err)
	}

	return catalog, nil
}

// SetCatalogOfReward перезаписывает таблицу каталога целиком.
func (db *Database) SetCatalogOfReward(ctx context.Context, catalog []CatalogOfReward) error {

	// _, err := db.Exec(ctx, `
	// 	truncate table "catalog_of_reward"
	// `)
	// if err != nil {
	// 	return err
	// }
	db.ExecTx(ctx, func(tx pgx.Tx) error {
		_, err := tx.Exec(ctx, `delete from "catalog_of_reward"`)
		if err != nil {
			return fmt.Errorf("error deleting from catalog_of_reward: %w", err)
		}

		fmt.Printf("len of the catalog: %d\n", len(catalog))

		_, err = db.CopyFrom(ctx, pgx.Identifier{"catalog_of_reward"},
			[]string{"id", "name_of_reward", "count", "price", "note", "link_on_photo"},
			pgx.CopyFromSlice(len(catalog), func(i int) ([]any, error) {
				return []any{
					catalog[i].ID,
					catalog[i].NameOfReward,
					catalog[i].Count,
					catalog[i].Price,
					catalog[i].Note,
					catalog[i].LinkOnPhoto,
				}, nil
			}),
		)
		if err != nil {
			return err
		}

		return nil
	})

	return nil
}

func (db *Database) BeginTx(ctx context.Context) (pgx.Tx, error) {
	return db.Conn.BeginTx(ctx, pgx.TxOptions{})
}

func (db *Database) ExecTx(ctx context.Context, fn func(pgx.Tx) error) error {
	tx, err := db.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("error starting transaction: %w", err)
	}

	err = fn(tx)
	if err != nil {
		if rbErr := tx.Rollback(ctx); rbErr != nil {
			return fmt.Errorf("error rollback transaction %w", err)
		}
		return fmt.Errorf("error somewhere in transaction: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return fmt.Errorf("error commit transaction: %w", err)
	}

	return nil
}
