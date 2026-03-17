# Gemini AutoPromter

自動化提示詞工具，使用 Selenium + undetected_chromedriver 自動填入 Gemini 網頁輸入框，並支援自動下載經濟數據資料。

## 功能

### 基礎功能
- 讀取 txt 提示詞檔案
- 自動開啟 Gemini 網頁
- 手動確認後發送提示詞
- 支援多個提示詞檔案選擇

### 資料下載功能
- **FRED API** - 自動下載美國聯準會經濟數據
- **MacroMicro (財經M平方)** - 自動下載台灣與美國經濟指標
- **Stooq** - 自動下載股市指數資料
- 支援設定保留資料筆數
- 自動解析 MD 檔案定義的資料需求

### Gemini 整合
- 支援上傳 JSON 資料檔案至 Gemini
- 可在發送提示詞前先上傳資料

## 安裝

```bash
cd /home/datakey/myProject/opencode/autoPromter
pip install -r requirements.txt
```

## 使用方式

### 1. 準備提示詞檔案

在 `prompts/` 目錄下建立 `.txt` 檔案，每行一個提示詞：

```txt
# 這是註釋，會被忽略
第一個提示詞
第二個提示詞
第三個提示詞
```

### 2. 準備資料需求檔案（可選）

在 `dataRequireList/` 目錄下建立 `.md` 檔案，定義要下載的資料：

```markdown
# 範例資料需求

## 自FRED獲取資料列表

### 使用FRED API取得資料
FRED API Key : your_api_key_here

### 所需資料列表
1. 名目GDP : GDP
2. CPI : CPIAUCSL

## 自macromicro獲取資料列表
1. 美國-ISM-PMI : https://www.macromicro.me/series/265/ism-pmi
```

### 3. 運行程式

```bash
python main.py
```

### 4. 操作流程

1. 輸入 `y` 使用現有登入會話，或 `n` 建立新會話
2. 輸入數字選擇提示詞檔案
3. 選擇是否下載資料 [y/n]
4. 如果選擇下載：
   - 選擇資料需求 MD 檔案
   - 程式會自動從 FRED、MacroMicro、Stooq 下載資料
   - 資料會儲存為 JSON 檔案
5. 瀏覽器會開啟
   - 選擇 `y`：會使用之前的登入資訊
   - 選擇 `n`：如果尚未登入，請手動登入 Gemini
6. 登入後按 Enter 繼續
7. 選擇是否上傳 JSON 資料到 Gemini [y/n]
8. 程式會顯示下一條提示詞
9. 按 **Enter** 或 **g** 發送提示詞
10. 按 **q** 退出
11. 全部完成後，按 **q** 關閉瀏覽器

## 目錄結構

```
autoPromter/
├── main.py              # 主程式
├── config.py            # 設定
├── browser/
│   └── driver.py       # 瀏覽器初始化
├── automation/
│   └── gemini.py       # Gemini 交互
├── utils/
│   ├── prompt_reader.py        # 提示詞讀取
│   └── data_require_list_reader.py  # 資料需求讀取
├── data_collector/
│   └── __init__.py    # 資料下載模組
├── prompts/           # 提示詞存放目錄
├── dataRequireList/   # 資料需求 MD 檔目錄
├── session/           # 瀏覽器 session（自動生成）
└── requirements.txt
```

## 設定

修改 `config.py` 調整參數：

| 參數 | 說明 | 預設 |
|------|------|------|
| `GEMINI_URL` | Gemini 網址 | https://gemini.google.com/ |
| `TIMEOUT` | 元素等待時間 | 30 秒 |
| `IMPLICIT_WAIT` | 隱式等待時間 | 10 秒 |
| `INPUT_DELAY_MIN` | 輸入最小延遲 | 0.05 秒 |
| `INPUT_DELAY_MAX` | 輸入最大延遲 | 0.15 秒 |
| `AFTER_SUBMIT_DELAY` | 提交後延遲 | 3 秒 |
| `DATA_KEEP_COUNT` | 下載資料保留筆數 | 100 |

## 資料來源支援

### FRED 資料代碼範例
- `GDP` - 名目 GDP
- `CPIAUCSL` - 名目 CPI
- `PCEPI` - 名目 PCE
- `DGS10` - 10年公債殖利率
- `INDPRO` - 工業生產指數

### MacroMicro 資料類型
- 台灣經濟指標（PMI、外銷訂單、存貨率等）
- 美國經濟指標（ISM-PMI、FINRA 融資餘額等）
- 落後/領先指標

### Stooq 資料類型
- 股市指數（S&P500、NASDAQ 等）
- 個股股價資料

## 注意事項

- 選擇 `y` 會使用現有登入會話（無需重複登入）
- 選擇 `n` 會清除登入資料並建立新會話
- 登入後關閉瀏覽器時，請按 **q** 正常退出，避免 session 資料損壞
- 提示詞中不能有換行符，會被自動移除
- 輸入框選擇器可能隨 Gemini 版本更新而變動
- 下載 MacroMicro 資料時可能需要處理驗證碼
- FRED API Key 需自行申請取得，自行填入到對應的.md檔案內
# autoPromter
