#!/usr/bin/env python3
"""Build catalog.json (speakers -> faces, emotes) for the story editor from the game files.

  python3 tools/build_editor_catalog.py [--game /workspace/tg/base] [--out catalog.json]

Sources (re-run whenever the game grows):
  - datafiles/portraits/portrait_spec.json (tools/portrait_spec.py) : speakers, sets, faces, effect layers
  - tools/storyboard_convert.py : TSV cells / portrait dicts per combination, TEXT_PORTRAITS, EMOTE_NUMBERS
  - docs/event_format.md : emote number/key/Chinese name table
Only names/keys are written (no story text, no art).
"""
import argparse, importlib.util, json, os, re, sys

# 2026-10-17 (viewer_fx): speakers, faces, sets (一般／秘湯) and effect layers all come from the game's
# datafiles/portraits/portrait_spec.json via tools/portrait_spec.py — the same spec the game's
# portrait viewer, the event player and tools/storyboard_convert.py use. Each face lists only the
# mask combinations the art really has ("combos"); each combo carries the exact TSV cell and the
# converter's own portrait dict (sprite / frame / spec), so editor -> TSV -> JSON cannot drift.
FX_KEY = {1: "blush", 2: "sweat", 4: "body", 8: "tears"}
FX_WORD = {1: "臉紅", 4: "泡後身體", 8: "眼淚"}

def load_converter(game):
    sys.path.insert(0, os.path.join(game, "tools"))
    p = os.path.join(game, "tools", "storyboard_convert.py")
    spec = importlib.util.spec_from_file_location("sbc", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def cell_for(c, s, f, m):
    words = (["秘湯"] if s["id"] == "onsen" else []) + [f["label"]]
    words += [FX_WORD.get(b, "秘湯汗" if s["id"] == "onsen" else "流汗") for b in (1, 2, 4, 8) if m & b]
    return c["words"][0] + "，" + "＋".join(words)

class Rep:
    def __init__(self): self.errors, self.warnings, self.missing_art, self.suggest = [], [], [], []

def emote_names(game):
    doc = open(os.path.join(game, "docs", "event_format.md"), encoding="utf-8").read()
    names = {}
    for n, key, zh in re.findall(r"\|\s*(\d+)\s*\|\s*([a-z]+)\s*\|\s*([^|\s]+)\s*", doc):
        names[int(n)] = (key, zh)
    return names

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="/workspace/tg/base")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "catalog.json"))
    a = ap.parse_args()
    sbc = load_converter(a.game)
    sbc.PROJECT = a.game
    ps = sbc.portrait_spec
    speakers = []
    for c in ps.load()["characters"]:
        faces, legacy = [], []
        for st in c["sets"]:
            layers = [{"k": FX_KEY[l["bit"]], "label": l["label"]} for l in st["layers"]]
            for f in st["faces"]:
                combos = []
                for m in ps.masks(c["id"], st["id"]):
                    ops, _ = ps.resolve(c["id"], st["id"], f["key"], m)
                    if not ops:
                        continue
                    cell, rep = cell_for(c, st, f, m), Rep()
                    out = sbc.parse_portraits(cell, "catalog", rep)
                    if rep.errors or len(out) != 1:
                        sys.exit("converter disagrees with spec: %s %s" % (cell, rep.errors))
                    combos.append({"m": m, "cell": cell, "portrait": out[0]})
                key = ("秘湯・" if st["id"] == "onsen" else "") + f["label"]
                # 故意沒有效果的表情（歐菲受傷）不給效果按鈕，也不算缺圖
                none = f.get("fx") == "none_by_design"
                face_layers = [] if none else layers
                faces.append({"key": key, "set": st["id"], "face": f["key"], "layers": face_layers,
                              "by_design": none,
                              "ok": [x["m"] for x in combos], "combos": combos,
                              "sprite": combos[0]["portrait"]["sprite"], "frame": combos[0]["portrait"]["frame"]})
                # old exports wrote one key per FX frame (「平常流汗」); keep reading them
                if st["id"] == "normal":
                    for word, k, m in (("流汗", "sweat", 2), ("臉紅", "blush", 1)):
                        if m in faces[-1]["ok"]:
                            legacy.append({"key": key + word, "face": key, "sweat": k == "sweat", "blush": k == "blush"})
        for (who, word), spr in sbc.TEXT_PORTRAITS.items():
            if who == c["id"] and sbc.sprite_frames(spr) is None and not any(f["key"] == word for f in faces):
                faces.append({"key": word, "set": "normal", "face": "", "layers": [], "ok": [0], "missing": True,
                              "combos": [{"m": 0, "cell": c["words"][0] + "，" + word, "portrait": None}],
                              "sprite": spr, "frame": 0, "note": "還沒有圖（缺圖卡）"})
        speakers.append({"id": c["id"], "label": c["name"], "kind": "speech", "faces": faces, "legacy_faces": legacy})
    speakers.append({"id": "narrator", "label": "旁白", "kind": "narration", "faces": [],
                     "hint": "客觀敘述，台詞用全形括號（）包住；沒有名牌、沒有立繪"})
    names = emote_names(a.game)
    emotes = []
    for n, key in sorted(sbc.EMOTE_NUMBERS.items()):
        zh = names.get(n, (key, ""))[1]
        emotes.append({"n": n, "key": key, "label": ("%s #%d" % (zh, n)) if zh else ("#%d（未命名）" % n)})
    cat = {"format": "juicelab-editor-catalog-1", "speakers": speakers, "emotes": emotes}
    # 2026-10-17 (old_story_archive): old pre-rewrite story is frozen; the editor refuses these scenes / files.
    cat["archived"] = {"dir": sbc.ARCHIVE_DIR_NAME, "ids": sorted(sbc.ARCHIVED_IDS)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1); f.write("\n")
    print("wrote", a.out, {s["label"]: len(s["faces"]) for s in speakers}, "emotes", len(emotes))
    for s in speakers:
        for f in s["faces"]:
            print("  %s %s ok=%s" % (s["label"], f["key"], f.get("ok")))

if __name__ == "__main__":
    main()
