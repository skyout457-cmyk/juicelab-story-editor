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
| `who` | 必填。`catalog.json` 的 `speakers[].label`（歐克、歐菲、旁白）。2026-10-22 起有兩個沒有立繪的說話者：「骸骨軍需官」（立繪製作中）、「勇者 劍士」（勇者類一律只有名牌和台詞）；它們的 `faces` 是空的，表情欄顯示「（沒有立繪）」，效果都不能開，`catalog.json` 的 `hint`／`no_portrait` 來自遊戲的 `portrait_spec.json` |
| `face` | 必填（旁白為 `""`）。那個角色的 `faces[].key` |
| `blush` / `sweat` / `body` / `tears` | 選填。效果開關（臉紅／流汗〔秘湯套裝＝秘湯汗〕／泡後身體／眼淚），可以同時開；沒有就是 `false`。只能開美術真的有的組合（`catalog.json` 的 `faces[].ok`／`combos`，由遊戲的 `datafiles/portraits/portrait_spec.json` 產生）。舊檔的「平常流汗」鍵照樣讀（`legacy_faces`），舊檔沒有 `body`／`tears` 也照讀 |
| `emote` | 選填。表符名稱（`emotes[].label` 去掉 ` #N`，例 `驚訝`）；`""`＝沒有 |
| `text` | 台詞。中文標點用全形；旁白用全形（）包住 |

## 立繪效果（2026-10-17 viewer_fx）

角色、套裝（一般／秘湯）、表情、效果層全部來自遊戲的 **portrait_spec.json**（`docs/event_format.md`「Portrait spec」），
和遊戲裡廢堡測試室的立繪檢視器、劇情事件播放器、`tools/storyboard_convert.py` 用同一份規格、同一個畫法。
`python3 tools/build_editor_catalog.py --game <遊戲資料夾>` 重新產生 `catalog.json`；
每個組合的 TSV 文字與事件 JSON 都是轉檔器自己算的，所以編輯器 → TSV → 遊戲不會對不上。

- 「表情」選單：一般套裝直接寫表情名；秘湯套裝是「秘湯・表情」。
- 「效果」按鈕：只出現這個套裝有的層。按下去的組合美術沒有就停用（滑鼠停在上面會說缺什麼），已打開的永遠可以關。
- 換表情時，新表情沒有目前的組合：會明確關掉並提示，不偷偷換成別張。

每個角色有／缺的組合見遊戲 `docs/event_format.md`「Portrait spec」的表。

## 2026-10-17 spec_labels
- 秘湯效果層：臉紅、秘湯汗、泡後身體（身體紅潤＋高光＋水滴水痕永遠一起出現，是同一層；舊名「身體紅潤」「泡後」照樣可用）。
- 歐菲／艾瑪／瑪琪娜的秘湯目前只有預合成圖：無、臉紅＋秘湯汗、臉紅＋秘湯汗＋泡後身體；其他組合按鈕停用（缺圖），等美術交透明分層 PNG 後只要改規格資料。
- 歐克故意沒有秘湯套，不提供秘湯表情。歐菲的 5 個受傷表情故意沒有效果，不顯示效果按鈕、不算缺圖。
- 格子也可用「・」分隔：`赫蒂，秘湯・害羞・臉紅・泡後身體`。
