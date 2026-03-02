package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"

	"github.com/xuri/excelize/v2"
)

var YANDEX_API_KEY = os.Getenv("YANDEX_API_KEY")

type YandexDisk struct {
	token  string
	client *http.Client
}

func NewYandexDisk() *YandexDisk {
	yd := &YandexDisk{
		token:  YANDEX_API_KEY,
		client: http.DefaultClient,
	}
	return yd
}

type YandexDiskUploadUrl struct {
	OperationID string `json:"operation_id"`
	Href        string `json:"href"`
	Method      string `json:"method"`
	Templated   bool   `json:"templated"`
}

func (yd *YandexDisk) getDownloadUrl(path string) (string, error) {
	u := url.URL{
		Scheme: "https",
		Host:   "cloud-api.yandex.net",
		Path:   "/v1/disk/resources/download",
	}

	q := u.Query()

	q.Set("path", path)

	u.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", u.String(), nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "OAuth "+yd.token)

	res, err := yd.client.Do(req)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return "", fmt.Errorf("error code received in get upload url request: %s", res.Status)
	}

	var body YandexDiskUploadUrl
	if err := json.NewDecoder(res.Body).Decode(&body); err != nil {
		return "", fmt.Errorf("error decoding get upload url rquest body: %w", err)
	}

	return body.Href, nil

}

func (yd *YandexDisk) getUploadUrl(path string) (string, error) {
	u := url.URL{
		Scheme: "https",
		Host:   "cloud-api.yandex.net",
		Path:   "/v1/disk/resources/upload",
	}

	q := u.Query()

	q.Set("path", path)
	q.Set("overwrite", "true")

	u.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", u.String(), nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "OAuth "+yd.token)

	res, err := yd.client.Do(req)
	if err != nil {
		return "", err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return "", fmt.Errorf("error code received in get upload url request: %s", res.Status)
	}

	var body YandexDiskUploadUrl
	if err := json.NewDecoder(res.Body).Decode(&body); err != nil {
		return "", fmt.Errorf("error decoding get upload url rquest body: %w", err)
	}

	return body.Href, nil
}

func (yd *YandexDisk) DownloadXlsx(path string) (*excelize.File, error) {
	downloadUrl, err := yd.getDownloadUrl(path)
	if err != nil {
		return nil, err
	}

	res, err := yd.client.Get(downloadUrl)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error HTTP status [%d]", res.StatusCode)
	}

	xlsx, err := excelize.OpenReader(res.Body)
	if err != nil {
		return nil, fmt.Errorf("error opening XLSX: %w", err)
	}

	fmt.Println("dowloaded! ", res.Status)

	return xlsx, nil
}
func (yd *YandexDisk) UploadXlsx(path string, file *excelize.File) error {
	uploadURL, err := yd.getUploadUrl(path)
	if err != nil {
		return err
	}

	var buf bytes.Buffer

	if err := file.Write(&buf); err != nil {
		return fmt.Errorf("error writing Excel into buffer: %w", err)
	}

	req, err := http.NewRequest("PUT", uploadURL, &buf)
	if err != nil {
		return fmt.Errorf("error creating http-request: %w", err)
	}

	req.Header.Set("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	req.Header.Set("Content-Length", fmt.Sprintf("%d", buf.Len()))

	res, err := yd.client.Do(req)
	if err != nil {
		return fmt.Errorf("error sending upload request: %w", err)
	}
	defer res.Body.Close()

	if res.StatusCode != http.StatusCreated && res.StatusCode != http.StatusAccepted {
		return fmt.Errorf("error code received in upload request: %s", res.Status)
	}

	return nil
}
