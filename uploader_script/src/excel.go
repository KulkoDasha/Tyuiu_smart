package main

import (
	"fmt"
	"strconv"

	"github.com/xuri/excelize/v2"
)

func CreateMainTable(issuances []IssuanceOfRewards, users []UserExcelTable, catalog []CatalogOfReward) (*excelize.File, error) {
	f := excelize.NewFile()
	defer func() {
		if err := f.Close(); err != nil {
			fmt.Println(err)
		}
	}()

	// Users --------------------------------------------------------------------

	userHeaders := []string{
		"ID", "Телеграм ID", "ФИО", "Имя пользователя", "ТИУКоины", "Дата принятия заявки", "Модератор",
		"Структурное подразделение обучения", "Курс обучения", "Группа",
	}
	err := createSheet(f, "Участники", userHeaders, len(users), func(i int) ([]any, error) {
		return []any{
			users[i].ID, users[i].TgID, users[i].FullName, users[i].UserName, users[i].Tiukoins,
			users[i].ApprovalDate, users[i].ModeratorUsername, users[i].StructuralUnit, users[i].Course, users[i].Group}, nil
	})
	if err != nil {
		return nil, err
	}

	// Issuances-----------------------------------------------------------------

	issuanceHeaders := []string{
		"ID", "Телеграмм ID", "Имя пользователя", "ID поощрения", "Название поощрения",
		"Стоимость", "Дата заказа", "Статус", "Модератор",
	}
	err = createSheet(f, "Выдача поощрений", issuanceHeaders, len(issuances), func(i int) ([]any, error) {
		rewardID := ""
		if issuances[i].RewardID != nil {
			rewardID = strconv.Itoa(int(*issuances[i].RewardID))
		}
		return []any{
			issuances[i].ID, issuances[i].TgID, issuances[i].UserName, issuances[i].RewardID, issuances[i].NameOfReward,
			issuances[i].Price, issuances[i].OrderDate, issuances[i].Status, issuances[i].ModeratorUsername,
		}, nil
	})
	if err != nil {
		return nil, err
	}

	// Catalog ------------------------------------------------------------------

	catalogHeaders := []string{
		"ID", "Название поощрения", "Количество", "Цена", "Примечание", "Ссылка на фото",
	}
	err = createSheet(f, "Каталог поощрений", catalogHeaders, len(catalog), func(i int) ([]any, error) {
		return []any{
			catalog[i].ID, catalog[i].NameOfReward, catalog[i].Count, catalog[i].Price, catalog[i].Note, catalog[i].LinkOnPhoto,
		}, nil
	})

	if err := f.DeleteSheet("Sheet1"); err != nil {
		return nil, fmt.Errorf("error deleting default sheet [Sheet1]: %w", err)
	}

	return f, nil
}

func CreateEventApplicationTable(applications []EventApplication) (*excelize.File, error) {
	f := excelize.NewFile()
	defer func() {
		if err := f.Close(); err != nil {
			fmt.Println(err)
		}
	}()

	grouped := make(map[string][]EventApplication)
	for _, app := range applications {
		grouped[app.EventDirection] = append(grouped[app.EventDirection], app)
	}

	headers := []string{
		"ID", "Телеграмм_ID", "ФИО", "Имя пользователя", "Название Мероприятия", "Дата проведения мероприятия",
		"Место проведения мероприятия", "Роль", "Количество ТИУКоинов", "Время отправки заявки",
		"Статус заявки", "Модератор",
	}

	for direction, apps := range grouped {
		row := 1
		_, err := f.NewSheet(direction)
		if err != nil {
			return nil, fmt.Errorf("error creating sheet [%s]: %w", direction, err)
		}

		for col, header := range headers {
			cell, err := excelize.CoordinatesToCellName(col+1, row)
			if err != nil {
				return nil, err
			}

			if err := f.SetCellStr(direction, cell, header); err != nil {
				return nil, fmt.Errorf("error writing header in cell [%s]: %w", direction, err)
			}

		}
		row += 1

		for _, app := range apps {
			values := []any{
				app.ID, app.TgID, app.FullName, app.Username, app.EventDirection,
				app.EventName, app.DateOfEvent, app.EventPlace,
				app.EventRole, app.EventApplicationStatus, app.AmountTiukoins,
				app.Moderator,
			}

			for col, value := range values {
				cell, _ := excelize.CoordinatesToCellName(col+1, row)
				if err := f.SetCellValue(direction, cell, value); err != nil {
					return nil, fmt.Errorf("error writing data in cell [%s]: %w", cell, err)
				}
			}
			row += 1
		}
	}

	if err := f.DeleteSheet("Sheet1"); err != nil {
		return nil, fmt.Errorf("error deleting default sheet [Sheet1]: %w", err)
	}

	return f, nil
}

func createSheet(f *excelize.File, sheetName string, headers []string, length int, next func(i int) ([]any, error)) error {
	_, err := f.NewSheet(sheetName)
	if err != nil {
		return fmt.Errorf("error creating sheet [%s]: %w", sheetName, err)
	}

	row := 1

	for col, header := range headers {
		cell, err := excelize.CoordinatesToCellName(col+1, row)
		if err != nil {
			return err
		}

		if err := f.SetCellStr(sheetName, cell, header); err != nil {
			return fmt.Errorf("error writing header in cell [%s]: %w", sheetName, err)
		}
	}
	row += 1

	for i := range length {
		values, err := next(i)
		if err != nil {
			return err
		}

		for col, value := range values {
			cell, _ := excelize.CoordinatesToCellName(col+1, row)
			if err := f.SetCellValue(sheetName, cell, value); err != nil {
				return fmt.Errorf("error writing data in cell [%s]: %w", cell, err)
			}
		}
		row += 1
	}

	return nil

}
