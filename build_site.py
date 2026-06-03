# -*- coding: utf-8 -*-
"""
今日の12星座占い サイト自動生成（4カテゴリ版 v2）
====================================================
    swisseph(惑星位置) → zodiac_excel.compute_all(4カテゴリ) → 占いCSV(差し込み文) → HTML

人間の作業ゼロ。タスクスケジューラで毎朝叩けば、その日のページが output/ に出る。

v2 では総合運に加えて 仕事/恋愛/健康 の3カテゴリを、それぞれ本物の
カテゴリ別スコア(1〜5)で差し込む。1星座あたり4ブロック×12星座＝厚いページ。

使い方:
    python build_site.py                  # 今日のページを生成
    python build_site.py --date 2026-06-10
    python build_site.py --open           # 生成後ブラウザで開く
"""

import argparse
import csv
import datetime
import hashlib
import html
import os
import random

import planets
import zodiac_excel
import config

HERE = os.path.dirname(os.path.abspath(__file__))


def resolve_message_csv() -> str:
    """
    メッセージCSVの場所を解決する（最初に見つかったものを使う）。
      1. 環境変数 FORTUNE_MESSAGE_CSV（任意の上書き）
      2. リポジトリ同梱の data/noplaceholder_varied.csv（← クラウドCIでも動く）
      3. みみさんのデスクトップ占いフォルダ（ローカル開発の元データ）
    """
    candidates = [
        os.environ.get("FORTUNE_MESSAGE_CSV"),
        os.path.join(HERE, "data", "noplaceholder_varied.csv"),
        r"C:\Users\y5268\Desktop\占い\noplaceholder_varied.csv",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    raise FileNotFoundError(
        "メッセージCSVが見つかりません。data/noplaceholder_varied.csv を用意してください。"
    )

CATEGORIES = ["総合", "仕事", "恋愛", "健康"]
CAT_ICON = {"総合": "🔮", "仕事": "💼", "恋愛": "💕", "健康": "🌿"}

# 星(★)表示
STAR = {1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆", 4: "★★★★☆", 5: "★★★★★"}


# ──────────────────────────────────────────────
# ランク(1〜12) → CSVの rank_label へ変換
#   score(★1〜5)は compute_all が各カテゴリで本物を出すので変換不要。
# ──────────────────────────────────────────────
def rank_to_label(rank: int) -> str:
    """noplaceholder_varied.csv の rank_label に合わせる: 1位/上位/下位/最下位"""
    if rank == 1:
        return "1位"
    if rank == 12:
        return "最下位"
    if rank <= 6:
        return "上位"
    return "下位"


# ──────────────────────────────────────────────
# メッセージCSVの読み込みと引き当て
# ──────────────────────────────────────────────
def load_all_messages() -> dict:
    """{category: {(score, rank_label): [メッセージ...]}} を返す。"""
    table: dict = {c: {} for c in CATEGORIES}
    with open(resolve_message_csv(), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = row["category"]
            if cat not in table:
                continue
            key = (int(row["score"]), row["rank_label"])
            table[cat].setdefault(key, []).append(row["message"])
    return table


def date_seed(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)


def pick_message(cat_table: dict, score: int, label: str, sign: str,
                 category: str, date_str: str) -> str:
    """その日・その星座・そのカテゴリで安定した1文を選ぶ。"""
    variations = cat_table.get((score, label))
    if not variations:  # 念のためのフォールバック
        variations = next(iter(cat_table.values()))
    rng = random.Random(date_seed(date_str + sign + category + str(score) + label))
    return rng.choice(variations)


def pick_lucky_item(sign: str, date_str: str) -> tuple[str, str]:
    """星座×日付で安定したラッキーアイテムと楽天リンクを返す。"""
    rng = random.Random(date_seed(date_str + sign + "lucky"))
    item = rng.choice(config.LUCKY_ITEMS_DEFAULT)
    return item, config.make_rakuten_link(item)


# ──────────────────────────────────────────────
# 1日分のデータを組み立て
# ──────────────────────────────────────────────
def build_day(date: datetime.date) -> dict:
    date_str = date.isoformat()
    signs = planets.get_today_signs(date)          # 5天体の星座（自動計算）
    moon = planets.get_moon_phase(date)

    ranking = zodiac_excel.compute_all(
        signs["月"], signs["水星"], signs["金星"], signs["火星"], signs["木星"]
    )  # rank昇順 list[dict] each: rank, sign, scores={総合,仕事,恋愛,健康}, ...

    messages = load_all_messages()
    rows = []
    for r in ranking:
        rank = r["rank"]
        sign = r["sign"]
        label = rank_to_label(rank)
        cats = []
        for cat in CATEGORIES:
            score = r["scores"][cat]
            cats.append({
                "name": cat,
                "icon": CAT_ICON[cat],
                "score": score,
                "stars": STAR[score],
                "message": pick_message(messages[cat], score, label, sign, cat, date_str),
            })
        rows.append({
            "rank": rank,
            "sign": sign,
            "categories": cats,           # [総合, 仕事, 恋愛, 健康]
            "lucky_item": pick_lucky_item(sign, date_str),
        })
    return {"date": date_str, "signs": signs, "moon": moon, "rows": rows}


# ──────────────────────────────────────────────
# HTML出力
# ──────────────────────────────────────────────
def render_html(day: dict) -> str:
    e = html.escape
    date_str = day["date"]
    moon = day["moon"]
    signs = day["signs"]
    planet_line = " / ".join(f"{k}:{v}" for k, v in signs.items())

    cards = []
    for r in day["rows"]:
        item, link = r["lucky_item"]
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(r["rank"], "")

        cat_blocks = []
        for c in r["categories"]:
            cat_blocks.append(f"""
          <div class="cat">
            <div class="cat-head"><span class="cat-name">{c['icon']} {e(c['name'])}運</span>
              <span class="stars">{c['stars']}</span></div>
            <p class="msg">{e(c['message'])}</p>
          </div>""")

        affiliate = ""
        if config.ENABLE_AFFILIATE:
            affiliate = (
                f'<div class="lucky">🍀 今日のラッキーアイテム：'
                f'<a href="{e(link)}" target="_blank" rel="nofollow noopener">{e(item)}</a></div>'
            )

        cards.append(f"""
      <article class="card rank{r['rank']}">
        <div class="card-head">
          <span class="rank">{r['rank']}位 {medal}</span>
          <h2>{e(r['sign'])}</h2>
        </div>
        {''.join(cat_blocks)}
        {affiliate}
      </article>""")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>今日の12星座占い（{e(date_str)}）｜総合・仕事・恋愛・健康運ランキング</title>
<meta name="description" content="{e(date_str)}の12星座占い。総合運ランキングに加え、仕事運・恋愛運・健康運を本物の天体計算（スイス・エフェメリス）で毎日自動更新。">
<style>
  :root {{ --bg:#0f1020; --card:#1c1d33; --accent:#ffd86b; --text:#ececf5; --sub:#a9a9c6; --line:#2b2c47; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
         background:var(--bg); color:var(--text); line-height:1.7; }}
  header {{ text-align:center; padding:32px 16px 12px; }}
  header h1 {{ margin:0 0 6px; font-size:1.5rem; }}
  header .meta {{ color:var(--sub); font-size:.85rem; }}
  main {{ max-width:760px; margin:0 auto; padding:16px; display:grid; gap:14px; }}
  .card {{ background:var(--card); border-radius:14px; padding:18px 18px 14px; }}
  .card-head {{ display:flex; align-items:baseline; gap:10px; border-bottom:1px solid var(--line);
                padding-bottom:8px; margin-bottom:6px; }}
  .card-head .rank {{ color:var(--accent); font-weight:bold; font-size:.95rem; white-space:nowrap; }}
  .card-head h2 {{ margin:0; font-size:1.3rem; }}
  .cat {{ padding:6px 0; border-bottom:1px dashed var(--line); }}
  .cat:last-of-type {{ border-bottom:none; }}
  .cat-head {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
  .cat-name {{ font-size:.9rem; color:var(--text); }}
  .stars {{ color:var(--accent); letter-spacing:2px; font-size:.9rem; white-space:nowrap; }}
  .msg {{ margin:2px 0 0; font-size:.9rem; }}
  .lucky {{ font-size:.82rem; color:var(--sub); margin-top:10px; }}
  .lucky a {{ color:var(--accent); }}
  .card.rank1 {{ outline:2px solid var(--accent); }}
  footer {{ text-align:center; color:var(--sub); font-size:.78rem; padding:24px 16px 40px; }}
</style>
</head>
<body>
  <header>
    <h1>🔮 今日の12星座占い</h1>
    <div class="meta">{e(date_str)}　総合・仕事・恋愛・健康運ランキング</div>
    <div class="meta">🌙 月相：{e(moon['name'])}　／　天体：{e(planet_line)}</div>
  </header>
  <main>
    {''.join(cards)}
  </main>
  <footer>
    本物の天体計算（Swiss Ephemeris）にもとづいて毎日自動更新。<br>
    ※本コンテンツはエンターテインメントです。
  </footer>
</body>
</html>"""


def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windowsコンソールの絵文字対策
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="今日の12星座占いサイト生成")
    ap.add_argument("--date", help="生成日 YYYY-MM-DD（省略時は今日）")
    ap.add_argument("--out", default="output",
                    help="出力フォルダ（公開用は docs を指定。既定 output）")
    ap.add_argument("--open", action="store_true", help="生成後ブラウザで開く")
    args = ap.parse_args()

    date = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    day = build_day(date)
    htmltext = render_html(day)

    out_dir = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
    os.makedirs(out_dir, exist_ok=True)
    dated = os.path.join(out_dir, f"zodiac_{day['date']}.html")
    index = os.path.join(out_dir, "index.html")
    for path in (dated, index):
        with open(path, "w", encoding="utf-8") as f:
            f.write(htmltext)

    print(f"🌙 月相: {day['moon']['name']}")
    print(f"📅 {day['date']} の12星座ランキング（総合/仕事/恋愛/健康）:")
    for r in day["rows"]:
        s = r["categories"]
        line = " ".join(f"{c['name']}{c['score']}" for c in s)
        print(f"  {r['rank']:>2}位 {r['sign']:<6} [{line}]")
    print(f"\n💾 出力: {index}")
    print(f"        {dated}")

    if args.open:
        import webbrowser
        webbrowser.open("file:///" + index.replace("\\", "/"))


if __name__ == "__main__":
    main()
