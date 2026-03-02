package main

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"

	_ "github.com/joho/godotenv/autoload"
	"github.com/xuri/excelize/v2"
)

func main() {
	ctx := context.Background()

	db, err := ConnectDB(ctx, os.Getenv("DB_CREDENTIALS"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}
	defer db.Close(ctx)

	yd := NewYandexDisk()

	// Тянем основную таблицу из Яндекс Диска
	mainTable, err := yd.DownloadXlsx("Работа_с_участниками_конкурса.xlsx")
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Запрашиваем юзеров
	users, err := db.ListUser(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Создаем список юзреов, готовых для вставки в эксель таблицу
	excelUsers, err := normalizeUsers(users, mainTable)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Запрашиваем список поощрений
	issuances, err := db.ListIssuanceOfRewards(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Запрашиваем каталог
	catalog, err := db.ListCatalogOfReward(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Если таблицы не равны, то перезаписываем соответствующую таблицу БД
	ok, err := isCatalogsSame(catalog, mainTable)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}
	if !ok {
		updatedCatalog, err := getCatalog(mainTable)
		catalog = updatedCatalog
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s", err.Error())
		}

		if err := db.SetCatalogOfReward(ctx, updatedCatalog); err != nil {
			fmt.Fprintf(os.Stderr, "%s", err.Error())
		}
	}

	// Пересоздаем основную таблицу
	updatedMainTable, err := CreateMainTable(issuances, excelUsers, catalog)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Загружаем основную таблицу на диск
	if err := yd.UploadXlsx("Работа_с_участниками_конкурса.xlsx", updatedMainTable); err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Запрашиваем заявки на мероприятия
	apps, err := db.ListEventApplication(ctx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Создаем обновленную таблицу
	xlsx, err := CreateEventApplicationTable(apps)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	// Загружаем таблицу на диск
	err = yd.UploadXlsx("Заявки.xlsx", xlsx)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s", err.Error())
	}

	fmt.Println("Done!")
}

func isCatalogsSame(catalog []CatalogOfReward, mainTable *excelize.File) (bool, error) {
	// TODO вынести названия страниц в константы
	rows, err := mainTable.Rows("Каталог поощрений")
	if err != nil {
		return false, err
	}
	defer rows.Close()

	// Пропускаем загловки
	if !rows.Next() {
		return false, nil
	}
	catalogMap := make(map[int]CatalogOfReward, len(catalog))
	for _, item := range catalog {
		catalogMap[item.ID] = item
	}

	for rows.Next() {
		columns, err := rows.Columns()
		if err != nil {
			return false, err
		}

		id, err := strconv.Atoi(columns[0])
		if err != nil {
			return false, err
		}

		// Название предмета
		catalogItem, exists := catalogMap[id]
		if !exists {
			return false, nil
		}
		excelName := strings.TrimSpace(columns[1])
		if excelName != catalogItem.NameOfReward {
			return false, nil
		}

		// Количество мерча
		excelCount, err := strconv.Atoi(columns[2])
		if err != nil {
			return false, err
		}
		if excelCount != catalogItem.Count {
			return false, nil
		}

		// Цена предмета
		excelPrice, err := strconv.Atoi(columns[3])
		if err != nil {
			return false, err
		}
		if excelPrice != catalogItem.Price {
			return false, nil
		}

		delete(catalogMap, id)
	}

	return len(catalogMap) == 0, nil
}

func getCatalog(mainTable *excelize.File) ([]CatalogOfReward, error) {
	rows, err := mainTable.Rows("Каталог поощрений")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Пропускаем заголовки
	if !rows.Next() {
		return nil, fmt.Errorf("error empty sheet [%s]", "Каталог поощрений")
	}

	catalog := make([]CatalogOfReward, 0, 64)
	for rows.Next() {
		columns, err := rows.Columns()
		if err != nil {
			return nil, err
		}

		item := CatalogOfReward{}

		id, err := strconv.Atoi(columns[0])
		if err != nil {
			return nil, err
		}
		item.ID = id

		excelName := strings.TrimSpace(columns[1])
		item.NameOfReward = excelName

		excelCount, err := strconv.Atoi(columns[2])
		if err != nil {
			return nil, err
		}
		item.Count = excelCount

		excelPrice, err := strconv.Atoi(columns[3])
		if err != nil {
			return nil, err
		}
		item.Price = excelPrice

		excelNote := strings.TrimSpace(columns[4])
		item.Note = excelNote

		excelPhotoLink := strings.TrimSpace(columns[5])
		item.LinkOnPhoto = excelPhotoLink

		catalog = append(catalog, item)
	}

	return catalog, nil
}

func normalizeUsers(users []User, mainTable *excelize.File) ([]UserExcelTable, error) {
	rows, err := mainTable.Rows("Участники")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	if !rows.Next() {
		return nil, fmt.Errorf("error empty sheet [%s]", "Участники")
	}

	excelUsersMap := make(map[int][]string)

	for rows.Next() {
		columns, err := rows.Columns()
		if err != nil {
			return nil, err
		}

		tgID, err := strconv.Atoi(strings.TrimSpace(columns[0]))
		if err == nil {
			excelUsersMap[tgID] = columns
		}
	}

	result := make([]UserExcelTable, 0, len(users))

	for _, dbUser := range users {
		userExcel := UserExcelTable{
			User: dbUser,
		}

		if excelRow, exists := excelUsersMap[dbUser.ID]; exists {
			if len(excelRow) > 7 {
				userExcel.StructuralUnit = strings.TrimSpace(excelRow[7])
			}
			if len(excelRow) > 8 {
				userExcel.Course = strings.TrimSpace(excelRow[8])
			}
			if len(excelRow) > 9 {
				userExcel.Group = strings.TrimSpace(excelRow[9])
			}
		}
		result = append(result, userExcel)
	}

	return result, nil
}
