"""Japanese CV64 text mapping, verified against the supplied ROM's glyph atlas.

Keep unknown/control words visible. Never silently discard an unknown glyph.
"""
from __future__ import annotations
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIRAGANA = "あぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわをんぁ"
KATAKANA = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロワヲン"
KANJI_ROWS = [
    "毒物水危険息引付近村人契約書辛読",
    "男声量辺害島大事商売道具甲運秘名",
    "前俗言悪魔待下貴方敵城訪見者々優",
    "藤金噂地獄沙汰次第会何縁差上用際",
    "使呼出張同時間長話過気向十字勤君",
    "正真銘結噛見森私俺伯爵封印来子供",
    "放無茶眼治任素相手今安全金計世関",
    "係口奴一度忠告場離助噂通様体命惜",
    "早逃吸血鬼他休達催託聞心小配町火",
    "家父母友達連黒中捜頭思丈失渡落先",
    "抜脱古良代恐不日紀期数王伝説生再",
    "燎闇堕魂邪年眠揺起主神復活受継統",
    "宿従祖聖騎討伐立考戦雷鳴共破開知",
    "尊族少女救証力解限鍵爆破可能所也",
    "東倒必両親報氷遠理惨死終持忌太陽",
    "照国決棒未熟技弱点冬虫同然刃鳥後",
    "悔空別参客頂熱耀存文記買越合支払",
    "利額既成鼻的争増情入勢稼行失礼偉",
    "捕殺望身人裂勝滅欲歪罪汚覆漫食止",
    "包己呪遠駕激流比悪程越本完覚醒界",
    "足揶諦財僕転憶収尽唯誤算外尋貧暗",
    "火計平等化馬鹿断判変怖与白抗攻撃",
    "数反甘故郷帰悲放館庫鍵持十淵消滅",
    "確続現去勇農墓降丘当歩壊急幸結婚",
    "守神苦恨分殺蘇操回推術信愛希負押",
    "随違運末隠路発自害娘到底駄祖苦耐",
    "深恋染誇切刻盾越兄弟願給喜怒送惚",
    "浩答開意頼威建波彼捕驚精飢天糧直",
    "若度簡単百美読権牡裳想愉快目以臓",
    "初実録躍択定明頃園勘役割境葉装置",
    "弾作捧問部屋調忘衝効敬章施異常接",
    "認修性黙示世容星為削除在了鳥肉京",
    "医学断秘晶内浄液飲石硬燃螺旋状軌",
    "描飛広凱囲有網投斧射謎召唖誰幸贈",
    "固陣法植烈短縮牛没注視裏左塔庭鉄",
    "柵緑青処刑科万療剤剣木杭月灼熱替",
    "移扉閉央嶺仕掛棺桶遺鎮歌荒祝福図",
    "像傷二輪車炎壁雨骨溺罠沼舎砦隣浮",
    "順巨格組袋砂彫光実面哀華晴匠裸婦",
    "風側打肖画穴磁積香満居花窓住赫灯",
    "鏡寝景並特滑赤差盤飾富卓婿柱岩型",
    "難砕模進禁標泥乗速夜屈洞亀暖炉器",
    "寒嫌泉漂埋拠幻草似融準備星審号昇",
    "符応専廃捨畑震痕誘充走跳慎宝箱迂",
    "海旅束四野楽壺品札写材三台元駒僅",
    "還御求残念個各種沈廊坑闘電源挿捕",
    "損敗更位架昼泣裏冷汗廻",
]


def character_map() -> dict[int, str]:
    mapping = {i:chr(i+0x1E) for i in range(2,0x60)}
    mapping.update({0x60:"、",0x61:"？",0x62:"「",0x63:"」",0x64:"。",0x65:"：",0x66:"ー",0x67:"▶"})
    mapping.update({0x68+i:str(i) for i in range(10)})
    mapping.update({0x1000+i:c for i,c in enumerate(HIRAGANA)})
    mapping.update({0x2000+i:c for i,c in enumerate(KATAKANA)})
    mapping[0x2050] = "ヴ"
    for row_no,row in enumerate(KANJI_ROWS):
        if len(row) > 16:
            raise ValueError(f"Too many glyphs in row {row_no:02X}: {len(row)} {row}")
        mapping.update({0x3000+row_no*16+i:c for i,c in enumerate(row)})
    mapping.update({0x3015:"覧",0x301E:"私",0x302C:"冒",0x304E:"動",
                    0x3054:"強",0x3086:"味",0x3089:"誰",0x308A:"願",
                    0x309C:"夫",0x309D:"疲",0x30D0:"導",0x30D4:"感",
                    0x3114:"界",0x3138:"要",0x3141:"我",0x3142:"絶",0x3143:"対",
                    0x3155:"愚",0x3202:"新",0x3263:"組",0x3265:"砂",0x326C:"噴"})
    mapping[0x65] = "・"
    # Reviewed against complete words in the supplied script. Tiny 16px glyphs
    # such as 最/結 and 壁/鍵 are unreliable when read in isolation.
    mapping.update({
        0x3014:'巻',0x301C:'申',0x3030:'譲',0x3044:'伺',0x3053:'最',0x3057:'迷',
        0x30B0:'漆',0x30C8:'若',0x30D9:'壁',0x30E6:'永',0x30F3:'様',
        0x3107:'幾',0x3117:'始',0x3120:'楯',0x3127:'救',0x312D:'侵',
        0x3133:'凌',0x313F:'果',0x3147:'取',0x314D:'費',0x3150:'込',0x3157:'惑',
        0x3160:'教',0x316C:'士',0x3187:'繰',0x3189:'避',0x3191:'運',0x3195:'爆',
        0x3198:'女',0x319B:'徒',0x319C:'奪',0x319D:'苦',0x319F:'浅',
        0x31A0:'経',0x31A1:'深',0x31A6:'迷',0x31B0:'造',0x31B4:'顔',0x31B6:'嬢',
        0x31BD:'天',0x31BE:'緒',0x31C6:'貌',0x31D3:'選',0x31DC:'壊',0x31E2:'拷',0x31EA:'紋',
        0x31FC:'了',0x31FF:'原',0x3203:'秘',0x3213:'範',0x3214:'囲',0x3216:'線',0x321C:'喚',
        0x321D:'購',0x321E:'棄',0x3227:'午',0x322B:'表',0x3244:'頑',0x3250:'像',
        0x3255:'炎',0x3256:'襲',0x325A:'因',0x325C:'含',0x325D:'皆',0x325E:'悶',
        0x3264:'袋',0x327E:'嫌',0x3287:'基',0x3288:'絵',0x328A:'壺',0x328C:'派',0x328F:'変',0x3292:'機',
        0x329A:'属',0x32A1:'鎌',0x32A2:'臭',0x32A5:'搬',0x32A9:'設',0x32AD:'番',
        0x32B5:'械',0x32B8:'添',0x32BD:'重',0x32C1:'蔵',0x32C2:'東',0x32C3:'西',0x32C4:'野',0x32C5:'集',
        0x32C6:'質',0x32C8:'机',0x32CF:'順',0x32D9:'館',0x32E2:'戻',0x32E7:'裏'
    })
    mapping[0x3195]='発'
    mapping.update({0x3185:'終',0x3192:'末',0x31C7:'犠',0x31C8:'牲',0x31F5:'空',0x31F7:'量'})
    mapping.update({0x30F9:'尽',0x30FE:'愚',0x3148:'戻',0x3155:'馬',0x3183:'返',
                    0x3194:'路',0x3196:'自',0x3197:'害',0x3199:'到',0x319A:'底',
                    0x31A6:'盾',0x31DD:'薬',0x328E:'色',0x32A1:'釜',0x32A4:'誘',
                    0x32B0:'得',0x32DE:'換',0x32E2:'更'})
    return mapping


CHARACTERS = character_map()


def decode_words(words: list[int]) -> str:
    parts = []
    for w in words:
        if w == 0: parts.append("<END>")
        elif w == 1: parts.append("\n")
        elif w == 0xFFFF: parts.append("<PAGE>")
        elif w in CHARACTERS: parts.append(CHARACTERS[w])
        else: parts.append(f"<{w:04X}>")
    return "".join(parts)


def scan_messages(data: bytes) -> list[dict]:
    records = []
    pos = 0
    while pos < len(data)-8:
        w = struct.unpack_from(">H", data, pos)[0]
        if w & 0xFF00 != 0xA000:
            pos += 2
            continue
        start = pos
        words = [w]
        cursor = pos + 2
        glyphs = 0
        japanese = 0
        while cursor < min(len(data)-1,start+0x2000):
            w = struct.unpack_from(">H",data,cursor)[0]
            if w in (0,0xFFFF):
                words.append(w)
                cursor += 2
                break
            if w not in CHARACTERS and w != 1 and not 0xA100 <= w <= 0xAFFF:
                break
            glyphs += int(w in CHARACTERS)
            japanese += int(0x1000 <= w <= 0x3FFF)
            words.append(w)
            cursor += 2
        if words[-1] in (0,0xFFFF) and glyphs >= 2:
            records.append(dict(offset=start,end=cursor,words=words,text=decode_words(words),
                                glyphs=glyphs,japanese=japanese))
            pos = cursor
        else:
            pos += 2
    return records


def export() -> None:
    manifest = json.loads((ROOT/"work/manifest.json").read_text())
    all_records = []
    sources = [("rom",(ROOT/"work/original.z64").read_bytes()[:manifest["assets"][0]["start"]])]
    for asset in manifest["assets"]:
        sources.append((f"asset_{asset['id']:03d}_{asset['reference_name']}",
                        (ROOT/"work/assets"/asset["file"]).read_bytes()))
    for name,data in sources:
        for record in scan_messages(data):
            record["source"] = name
            record["key"] = f"{name}:{record['offset']:06X}"
            all_records.append(record)
    (ROOT/"analysis/messages.json").write_text(json.dumps(all_records,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=[]
    for record in all_records:
        lines.extend([f"[{record['key']}]",record["text"],""])
    (ROOT/"analysis/messages.txt").write_text("\n".join(lines),encoding="utf-8")
    (ROOT/"analysis/character_map.json").write_text(json.dumps({f"{k:04X}":v for k,v in CHARACTERS.items()},ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(all_records)} messages, {sum(r['glyphs'] for r in all_records)} glyphs")
    for n,row in enumerate(KANJI_ROWS):
        if len(row)!=16 and n<46: print(f"Check short row {n:02X}: {len(row)} {row}")


if __name__ == "__main__":
    export()
