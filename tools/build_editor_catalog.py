#!/usr/bin/env python3
"""Build catalog.json (speakers -> faces, emotes) for the story editor from the game files.

  python3 tools/build_editor_catalog.py [--game /workspace/tg/base] [--out catalog.json]

Sources (re-run whenever the game grows):
  - tools/storyboard_convert.py : FACE_KEYS, TEXT_PORTRAITS, FX_FRAMES, EMOTE_NUMBERS
  - scripts/scr_orc_portrait, scr_ophelia_portrait : portrait expression enums
  - docs/event_format.md : emote number/key/Chinese name table
Only names/keys are written (no story text, no art).
"""
import argparse, importlib.util, json, os, re

# Chinese labels for the portrait enums (enum name -> label). Unknown enums get the English name.
ENUM_LABELS = {"Neutral": "平常", "Triangle": "三角嘴", "Smile": "微笑", "Gentle": "溫柔",
               "Worried": "擔心", "Sad": "難過", "Surprised": "驚訝", "Angry": "生氣",
               "Sleep": "睡著", "Shy": "害羞"}
# speakers shown in the editor: id -> (label, portrait enum script, sprite prefix)
SPEAKERS = [("orc", "歐克", "scr_orc_portrait", "OrcPortraitExpression"),
            ("ophelia", "歐菲", "scr_ophelia_portrait", "OpheliaPortraitExpression"),
            ("emma", "艾瑪", "scr_emma_portrait", "EmmaPortraitExpression"),
            ("makina", "瑪琪娜", "scr_makina_portrait", "MakinaPortraitExpression")]
# 2026-10-17 (editor_fx): 流汗／臉紅 are two independent toggles on every face. Availability comes
# from the converter's FX_LAYOUT (mask 臉紅 1 | 流汗 2 -> frame) checked against the real frame
# count in sprites/<name>/<name>.yy (sprite_frames, incl. the orc's virtual composite frame 3).
FX_KEYS = {"blush": 1, "sweat": 2, "both": 3}

def load_converter(game):
    p = os.path.join(game, "tools", "storyboard_convert.py")
    spec = importlib.util.spec_from_file_location("sbc", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def enum_names(game, script, enum):
    src = open(os.path.join(game, "scripts", script, script + ".gml"), encoding="utf-8").read()
    body = re.search(r"enum\s+%s\s*\{(.*?)\}" % enum, src, re.S).group(1)
    return [n for n, _ in re.findall(r"(\w+)\s*=\s*(\d+)", body)]

def emote_names(game):
    doc = open(os.path.join(game, "docs", "event_format.md"), encoding="utf-8").read()
    names = {}
    for n, key, zh in re.findall(r"\|\s*(\d+)\s*\|\s*([a-z]+)\s*\|\s*([^|\s]+)\s*", doc):
        names[int(n)] = (key, zh)
    return names

def face_fx(sbc, sid, spr):
    """{"sweat": frame|None, "blush": frame|None, "both": frame|None} for a base-expression sprite"""
    layout = getattr(sbc, "FX_LAYOUT", {}).get(sid, {0: 0})
    n = sbc.sprite_frames(spr) or 0
    return {k: (layout[m] if m in layout and layout[m] < n else None) for k, m in FX_KEYS.items()}

NO_FX = {"sweat": None, "blush": None, "both": None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="/workspace/tg/base")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "catalog.json"))
    a = ap.parse_args()
    sbc = load_converter(a.game)
    sbc.PROJECT = a.game
    speakers = []
    for sid, label, script, enum in SPEAKERS:
        faces = []
        for e in enum_names(a.game, script, enum):
            spr = "spr_%s_portrait_%s" % (sid, e.lower())
            zh = ENUM_LABELS.get(e, e)
            if sbc.sprite_frames(spr) is None:
                continue  # enum entry without art: not offered
            faces.append({"key": zh, "sprite": spr, "frame": 0, "fx": face_fx(sbc, sid, spr)})
        for (who, word), spr in sbc.TEXT_PORTRAITS.items():
            if who == sid and not any(f["sprite"] == spr for f in faces):
                faces.append({"key": word, "sprite": spr, "frame": 0, "fx": dict(NO_FX), "note": "立繪可能還在重畫"})
        for (who, key), (spr, fr) in sbc.FACE_KEYS.items():
            if who == sid:
                faces.append({"key": key, "sprite": spr, "frame": fr, "fx": dict(NO_FX)})
        # old exports wrote one key per FX frame (「平常流汗」); keep reading them
        legacy = []
        for f in faces:
            for word, k in (("流汗", "sweat"), ("臉紅", "blush")):
                if f["fx"][k] is not None:
                    legacy.append({"key": f["key"] + word, "face": f["key"], "sweat": k == "sweat", "blush": k == "blush"})
        speakers.append({"id": sid, "label": label, "kind": "speech", "faces": faces, "legacy_faces": legacy})
    speakers.append({"id": "narrator", "label": "旁白", "kind": "narration", "faces": [],
                     "hint": "客觀敘述，台詞用全形括號（）包住；沒有名牌、沒有立繪"})
    names = emote_names(a.game)
    emotes = []
    for n, key in sorted(sbc.EMOTE_NUMBERS.items()):
        zh = names.get(n, (key, ""))[1]
        emotes.append({"n": n, "key": key, "label": ("%s #%d" % (zh, n)) if zh else ("#%d（未命名）" % n)})
    cat = {"format": "juicelab-editor-catalog-1", "speakers": speakers, "emotes": emotes}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1); f.write("\n")
    print("wrote", a.out, {s["label"]: len(s["faces"]) for s in speakers}, "emotes", len(emotes))
    for s in speakers:
        for f in s["faces"]:
            print("  %s %s %s %s" % (s["label"], f["key"], f["sprite"], f.get("fx")))

if __name__ == "__main__":
    main()
