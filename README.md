# JuiceLab 劇情編輯器

手機用的劇情輸入表單（純靜態網頁，沒有後端；劇情只存在手機的 localStorage 和你自己存出的檔案）。

- 選項清單在 `catalog.json`，由 `tools/build_editor_catalog.py` 從遊戲檔產生（只有角色名、表情鍵、表符名稱，沒有劇情或圖）：
  `python3 tools/build_editor_catalog.py --game <遊戲專案資料夾>`
- 存檔：手機跳出分享選單（Web Share API），選雲端硬碟存檔；不支援時改成下載。「開啟檔案」可以重新讀回。

## 匯出格式 `juicelab-story-editor-1`

```json
{
  "format": "juicelab-story-editor-1",
  "version": 1,
  "exported": "2026-10-14T12:00:00.000Z",
  "scene": {"id": "場景 id（自動產生）", "title": "場景名稱"},
  "lines": [
    {"type": "line", "who": "歐克", "face": "三角嘴", "emote": "驚訝", "text": "……！"},
    {"type": "action", "text": "鏡頭慢慢推近火堆，歐克往後退半步"},
    {"type": "line", "who": "旁白", "face": "", "emote": "", "text": "（雨聲變大了）"}
  ]
}
```

| 欄位 | 內容 |
|---|---|
| `type` | `line`＝台詞、`action`＝🎬 動作卡（只有 `text`：鏡頭、走位、人物動作的文字說明）。舊檔沒有 `type` 一律當 `line` |
| `who` | 必填。`catalog.json` 的 `speakers[].label`（歐克、歐菲、旁白） |
| `face` | 必填（旁白為 `""`）。那個角色的 `faces[].key` |
| `emote` | 選填。表符名稱（`emotes[].label` 去掉 ` #N`，例 `驚訝`）；`""`＝沒有 |
| `text` | 台詞。中文標點用全形；旁白用全形（）包住 |
