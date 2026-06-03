# -*- coding: utf-8 -*-
"""
今日の惑星位置を swisseph で自動計算するモジュール。
=====================================================
これまで みみさんが Excel(星座占い.xlsx) に手入力していた
「月・水星・金星・火星・木星が今日いる星座」を、無人で算出する。

- swisseph の Moshier 内蔵エフェメリス(FLG_MOSEPH)を使うので
  天文データファイルのダウンロードは不要。
- 既存ツール(FortunePromptMaker/HoroscopeApp)には一切触れていない。

検証: 2026-06-03 の出力は、みみさんが Excel に入れていた
  月=やぎ座 / 水星=かに座 / 金星=かに座 / 火星=おうし座 / 木星=かに座
と完全一致する（= zodiac_excel.py のテストケースと同じ入力）。
"""

import datetime
import swisseph as swe

# 標準トロピカル12星座。黄経0度=おひつじ座から30度刻み。
SIGN_ORDER = [
    "おひつじ座", "おうし座", "ふたご座", "かに座", "しし座", "おとめ座",
    "てんびん座", "さそり座", "いて座", "やぎ座", "みずがめ座", "うお座",
]

# zodiac_excel.compute_overall() が必要とする5天体（順序は問わない）
BODIES = {
    "月":   swe.MOON,
    "水星": swe.MERCURY,
    "金星": swe.VENUS,
    "火星": swe.MARS,
    "木星": swe.JUPITER,
}

# データファイル不要・速度も取得
_FLAG = swe.FLG_MOSEPH | swe.FLG_SPEED


def lon_to_sign(lon: float) -> str:
    """黄経(度) → 標準12星座名。"""
    return SIGN_ORDER[int(lon % 360 // 30)]


def _julday(date: datetime.date) -> float:
    """その日の 0時UT のユリウス日。"""
    return swe.julday(date.year, date.month, date.day, 0.0)


def get_longitudes(date: datetime.date) -> dict:
    """5天体の黄経(度)を返す。{'月': 281.2, ...}"""
    jd = _julday(date)
    out = {}
    for name, body in BODIES.items():
        pos, _ = swe.calc_ut(jd, body, _FLAG)
        out[name] = pos[0]
    return out


def get_today_signs(date: datetime.date | None = None) -> dict:
    """
    5天体が今日いる星座を返す。
    戻り値: {'月':'やぎ座', '水星':'かに座', '金星':'かに座', '火星':'おうし座', '木星':'かに座'}
    そのまま zodiac_excel.compute_overall(**signs の順) に渡せる。
    """
    if date is None:
        date = datetime.date.today()
    return {name: lon_to_sign(lon) for name, lon in get_longitudes(date).items()}


# ──────────────────────────────────────────────
# 月相（差別化要素。今はスコア補正せず「表示」だけ）
# ──────────────────────────────────────────────
MOON_PHASES = [
    (0,   "新月"),     (45,  "三日月"),   (90,  "上弦の月"),
    (135, "十三夜月"), (180, "満月"),     (225, "十八夜月"),
    (270, "下弦の月"), (315, "二十六夜月"),
]


def get_moon_phase(date: datetime.date | None = None) -> dict:
    """太陽-月の離角から月相を求める。戻り値 {'angle':.., 'name':..}"""
    if date is None:
        date = datetime.date.today()
    jd = _julday(date)
    sun, _ = swe.calc_ut(jd, swe.SUN, _FLAG)
    moon, _ = swe.calc_ut(jd, swe.MOON, _FLAG)
    elong = (moon[0] - sun[0]) % 360
    # 一番近い区切りの名前を採用
    name = min(MOON_PHASES, key=lambda p: min(abs(elong - p[0]), 360 - abs(elong - p[0])))[1]
    return {"angle": round(elong, 1), "name": name}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    d = datetime.date.today()
    if len(sys.argv) > 1:
        d = datetime.date.fromisoformat(sys.argv[1])
    print(f"=== {d} の惑星位置 ===")
    for name, lon in get_longitudes(d).items():
        print(f"  {name:<4} 黄経{lon:7.2f}度 → {lon_to_sign(lon)}")
    mp = get_moon_phase(d)
    print(f"  月相: {mp['name']}（離角{mp['angle']}度）")
