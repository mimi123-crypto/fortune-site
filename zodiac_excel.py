# -*- coding: utf-8 -*-
"""
星座占い.xlsx の「全体運」ランキング計算を忠実にPython移植したもの。
-------------------------------------------------------------------
出典: みみさんの運用中Excel  C:\\Users\\y5268\\Downloads\\星座占い.xlsx
  シート1: ルックアップ表（星座/エレメント相性/角度スコア/星）
  シート2: メイン計算ブロック（A12:Z23）の数式を1セルずつ移植
※Excelは変更していない。数式を読み取って再現したもの。

入力: 月・水星・金星・火星・木星 が今日いる星座（名前 or 角度）
出力: 12星座の全体運ランキング
"""

# シート1!A2:E13 …… (星座名, 陰陽, エレメント, 角度)  ※Excelの行順そのまま
SIGNS = [
    ("いて座",   "陽", "火",   0),
    ("さそり座", "陰", "水",  30),
    ("てんびん座","陽", "風",  60),
    ("おとめ座", "陰", "地",  90),
    ("しし座",   "陽", "火", 120),
    ("かに座",   "陰", "水", 150),
    ("ふたご座", "陽", "風", 180),
    ("おうし座", "陰", "地", 210),
    ("おひつじ座","陽", "火", 240),
    ("うお座",   "陰", "水", 270),
    ("みずがめ座","陽", "風", 300),
    ("やぎ座",   "陰", "地", 330),
]

# 角度→星座（経度を入れたとき用）
def angle_to_sign_name(deg):
    deg = deg % 360
    # SIGNSの角度は 0,30,...330。30度刻みで対応
    idx = int(deg // 30)
    for name, _, _, a in SIGNS:
        if a == idx * 30:
            return name
    return SIGNS[0][0]

# シート1!C16:D31 …… エレメント相性（"火火"=3 など）
ELEMENT_PAIR = {
    "火火": 3, "火水": 2, "火風": 3, "火地": 1,
    "水火": 2, "水水": 3, "水風": 1, "水地": 3,
    "風火": 3, "風水": 1, "風風": 3, "風地": 2,
    "地火": 1, "地水": 3, "地風": 2, "地地": 3,
}

# シート1!A34:B45 …… 角度差→スコア
ANGLE_SCORE = {0: 1, 30: 4, 60: 3, 90: 5, 120: 2, 150: 4,
               180: 4, 210: 4, 240: 2, 270: 5, 300: 3, 330: 4}

# シート1!A48:B52 …… スコア→星
STARS = {1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆", 4: "★★★★☆", 5: "★★★★★"}

# 索引用
_SIGN_BY_NAME = {s[0]: s for s in SIGNS}


def excel_rank(value, ref_values):
    """ExcelのRANK(降順)。最大値=1位。同値は同順位。= 1 + (自分より大きい個数)。"""
    return 1 + sum(1 for v in ref_values if v > value)


def _yinyang(sign_name):
    return _SIGN_BY_NAME[sign_name][1]

def _element(sign_name):
    return _SIGN_BY_NAME[sign_name][2]

def _angle(sign_name):
    return _SIGN_BY_NAME[sign_name][3]


# カテゴリ→使用惑星（シート2 C27:F27 = 6 - angle_score）
# 総合←月, 仕事←水星, 恋愛←金星, 健康←火星
CATEGORY_ORDER = ["総合", "仕事", "恋愛", "健康"]


def _best_category(total, work, love, health):
    """シート2 K〜Q列の最強カテゴリ選定（同点時 総合>仕事>恋愛>健康）。"""
    if total >= max(work, love, health):
        return "総合", total
    if work >= max(love, health):
        return "仕事", work
    if love >= health:
        return "恋愛", love
    return "健康", health


def compute_all(moon, mercury, venus, mars, jupiter):
    """
    Excelシート2を丸ごと再現。
    引数は星座名（例 "やぎ座"）。
    戻り値: 順位昇順の list[dict]。各dict:
      rank, sign, y,
      scores={総合,仕事,恋愛,健康}(各1〜5),
      breakdown="1位おうし座:総合4/仕事3/恋愛3/健康5",
      board_cat, board_score, board_line="1位おうし座:健康★★★★★"
    """
    p1_yin = _yinyang(moon)      # B8
    p1_elem = _element(moon)     # B9
    angB = _angle(moon)          # B10  月
    angC = _angle(mercury)       # C10  水星
    angD = _angle(venus)         # D10  金星
    angE = _angle(mars)          # E10  火星
    angF = _angle(jupiter)       # F10  木星

    n = len(SIGNS)
    B = [0]*n; C = [0]*n; D = [0]*n; E = [0]*n
    J = [0]*n; K = [0]*n; N = [0]*n; O = [0]*n
    R = [0]*n; S = [0]*n; V = [0]*n; W = [0]*n

    for i, (name, yin, elem, a) in enumerate(SIGNS):
        B[i] = 1 if p1_yin == yin else 0                 # 陰陽一致
        C[i] = ELEMENT_PAIR[p1_elem + elem]              # エレメント相性
        D[i] = abs(a - angB); E[i] = ANGLE_SCORE[D[i]]   # 月への角度
        J[i] = abs(a - angC); K[i] = ANGLE_SCORE[J[i]]   # 水星
        N[i] = abs(a - angD); O[i] = ANGLE_SCORE[N[i]]   # 金星
        R[i] = abs(a - angE); S[i] = ANGLE_SCORE[R[i]]   # 火星
        V[i] = abs(a - angF); W[i] = ANGLE_SCORE[V[i]]   # 木星

    # ランク列（参照先に注意：Excelの数式通り）
    F = [excel_rank(E[i], E) for i in range(n)]          # RANK(E, E)
    L = [excel_rank(K[i], K) for i in range(n)]          # RANK(K, K)
    P = [excel_rank(O[i], K) for i in range(n)]          # RANK(O, K) ←K参照
    T = [excel_rank(S[i], K) for i in range(n)]          # RANK(S, K) ←K参照
    X = [excel_rank(W[i], E) / 10 for i in range(n)]     # RANK(W, E)/10

    Y = [0.0]*n
    for i in range(n):
        G = B[i] + C[i]
        H = G + F[i]
        I = H * 3                # I10=3
        M = I + L[i]
        Q = M + P[i]
        U = Q + T[i]
        Y[i] = U + X[i]

    Z = [excel_rank(Y[i], Y) for i in range(n)]

    rows = []
    for i, (name, *_rest) in enumerate(SIGNS):
        total  = 6 - E[i]   # 総合 ← 月
        work   = 6 - K[i]   # 仕事 ← 水星
        love   = 6 - O[i]   # 恋愛 ← 金星
        health = 6 - S[i]   # 健康 ← 火星
        bcat, bsc = _best_category(total, work, love, health)
        rank = Z[i]
        rows.append({
            "rank": rank,
            "sign": name,
            "y": round(Y[i], 3),
            "scores": {"総合": total, "仕事": work, "恋愛": love, "健康": health},
            "breakdown": f"{rank}位{name}:総合{total}/仕事{work}/恋愛{love}/健康{health}",
            "board_cat": bcat,
            "board_score": bsc,
            "board_line": f"{rank}位{name}:{bcat}{STARS[bsc]}",
        })
    rows.sort(key=lambda r: r["rank"])
    return rows


def compute_overall(moon, mercury, venus, mars, jupiter):
    """全体運ランキングだけ欲しいとき用の薄いラッパ。[(順位, 星座名, Y値), ...]"""
    return [(r["rank"], r["sign"], r["y"])
            for r in compute_all(moon, mercury, venus, mars, jupiter)]


def board_text(moon, mercury, venus, mars, jupiter):
    """みみさんの配信ボード形式（順位順・各星座の最強カテゴリ＋星）を生成。"""
    rows = compute_all(moon, mercury, venus, mars, jupiter)
    return "\n".join(r["board_line"] for r in rows)


if __name__ == "__main__":
    # ===== 検証：Excelの現在の入力(B7:F7)と全出力に一致するか =====
    # 月=やぎ座, 水星=かに座, 金星=かに座, 火星=おうし座, 木星=かに座
    rows = compute_all("やぎ座", "かに座", "かに座", "おうし座", "かに座")

    # Excel正解：内訳(G列)
    expected_breakdown = {
        "いて座": "9位いて座:総合2/仕事2/恋愛2/健康2",
        "さそり座": "5位さそり座:総合3/仕事4/恋愛4/健康2",
        "てんびん座": "11位てんびん座:総合1/仕事1/恋愛1/健康2",
        "おとめ座": "2位おとめ座:総合4/仕事3/恋愛3/健康4",
        "しし座": "10位しし座:総合2/仕事2/恋愛2/健康1",
        "かに座": "6位かに座:総合2/仕事5/恋愛5/健康3",
        "ふたご座": "7位ふたご座:総合2/仕事2/恋愛2/健康2",
        "おうし座": "1位おうし座:総合4/仕事3/恋愛3/健康5",
        "おひつじ座": "12位おひつじ座:総合1/仕事1/恋愛1/健康2",
        "うお座": "3位うお座:総合3/仕事4/恋愛4/健康3",
        "みずがめ座": "8位みずがめ座:総合2/仕事2/恋愛2/健康1",
        "やぎ座": "4位やぎ座:総合5/仕事2/恋愛2/健康4",
    }
    # Excel正解：配信ボード(Q列、順位順)
    expected_board = (
        "1位おうし座:健康★★★★★\n2位おとめ座:総合★★★★☆\n3位うお座:仕事★★★★☆\n"
        "4位やぎ座:総合★★★★★\n5位さそり座:仕事★★★★☆\n6位かに座:仕事★★★★★\n"
        "7位ふたご座:総合★★☆☆☆\n8位みずがめ座:総合★★☆☆☆\n9位いて座:総合★★☆☆☆\n"
        "10位しし座:総合★★☆☆☆\n11位てんびん座:健康★★☆☆☆\n12位おひつじ座:健康★★☆☆☆"
    )

    print("===== ① 内訳（順位＋4カテゴリスコア）=====")
    ok = True
    for r in rows:
        exp = expected_breakdown[r["sign"]]
        mark = "✓" if r["breakdown"] == exp else "✗ NG"
        if r["breakdown"] != exp:
            ok = False
        print(f"  {r['breakdown']:<28} {mark}")

    print("\n===== ② 配信ボード（最強カテゴリ＋星）=====")
    got_board = board_text("やぎ座", "かに座", "かに座", "おうし座", "かに座")
    board_ok = got_board == expected_board
    print(got_board)
    print(f"\n  ボード一致: {'✓' if board_ok else '✗ NG'}")

    print()
    if ok and board_ok:
        print("🎉 完全一致：順位・4カテゴリ・配信ボードすべてExcelと一致")
    else:
        print("⚠ 不一致あり：要調整")
