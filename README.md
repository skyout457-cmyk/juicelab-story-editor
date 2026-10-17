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
    {"type": "line", "who": "歐克", "face": "三角嘴", "sweat": true, "blush": false, "emote": "驚訝", "text": "……！"},
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
| `sweat` / `blush` | 選填（2026-10-17）。流汗／臉紅開關，可以同時開。沒有就是 `false`。只能開那個表情真的有圖的組合（`catalog.json` 的 `faces[].fx`：`sweat`／`blush`／`both` → frame，`null`＝沒有圖，編輯器裡按鈕停用）。舊檔的「平常流汗」這種鍵照樣讀得進來（`legacy_faces`），讀進來就拆成表情＋開關 |
| `emote` | 選填。表符名稱（`emotes[].label` 去掉 ` #N`，例 `驚訝`）；`""`＝沒有 |
| `text` | 台詞。中文標點用全形；旁白用全形（）包住 |

## 流汗／臉紅（2026-10-17）

每一行「表符」旁邊有兩個按鈕「💧 流汗」「😳 臉紅」，可以只開一個、兩個一起開、或都不開。
那個角色／表情沒有某種組合的圖時，那顆按鈕會變灰、劃線（點不下去），不會偷偷換成別張圖；換表情時如果新表情沒有目前的組合，會關掉那個開關並跳提示。

| 角色 | 流汗 | 臉紅 | 流汗＋臉紅 | 依據 |
|---|---|---|---|---|
| 歐克（平常、三角嘴） | frame 1 | frame 2 | 有（frame 3＝遊戲裡用臉紅圖＋汗滴合成） | 3 張圖；`orc_portrait_draw` |
| 歐菲（9 種表情） | frame 2 | frame 1 | frame 3 | 8 張圖＝臉紅 1｜流汗 2｜淚 4（淚沒畫） |
| 歐菲（受傷系列 5 個） | — | — | — | 一張一個表情，沒有特效圖 |
| 艾瑪（9 種表情） | — | frame 1 | — | 2 張圖（沒有流汗圖） |
| 瑪琪娜（9 種表情） | frame 2 | frame 1 | frame 3 | 4 張圖 |
| 歐克得意、艾瑪含淚微笑 | — | — | — | 圖還沒進專案 |

`python3 tools/build_editor_catalog.py --game <遊戲專案>` 會從 sprites 的實際張數重算。
