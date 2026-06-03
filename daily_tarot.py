# -*- coding: utf-8 -*-
"""
今日の1枚タロット 投稿テキスト自動生成ツール
=================================================
みみさんの稼働中Tarotエンジンの意味データ(tarot_data.py)を使い、
X / Bluesky / note にコピペできる「今日の1枚タロット」投稿文を自動生成する。

特徴:
- GUI不要・コマンド1発。タスクスケジューラ等で無人実行できる。
- 日付シードなので「今日の1枚」は同じ日に何度実行しても同じカードになる。
- 既存ツール(C:\\pleiades\\...\\Tarot)には一切触れていない（データを移植しただけ）。

使い方:
    python daily_tarot.py              # 今日の1枚を生成
    python daily_tarot.py --date 2026-06-10   # 指定日で生成
    python daily_tarot.py --major      # 大アルカナ22枚のみから引く
    python daily_tarot.py --no-save    # ファイル保存せず画面表示のみ
"""

import argparse
import datetime
import hashlib
import os
import random

import tarot_data
import config


# ──────────────────────────────────────────────
# 投稿メッセージのテンプレート
#   カードの意味(キーワード)を {kw} に差し込む。複数あるので日付で選ぶ。
# ──────────────────────────────────────────────
UPRIGHT_TEMPLATES = [
    "今日のテーマは「{kw}」。流れは追い風です。素直に動いた人ほど運が開きます。",
    "キーワードは「{kw}」。迷ったら、前向きな方をえらんで大丈夫な日。",
    "今日のあなたを支えるのは「{kw}」の力。小さな一歩がちゃんと実ります。",
    "「{kw}」が今日の追い風。チャンスは思ったより身近にあります。",
]
REVERSE_TEMPLATES = [
    "今日は「{kw}」に注意。無理に進めず、一度立ち止まると整います。",
    "キーワードは「{kw}」。焦りは禁物。今日は守りを固める日。",
    "「{kw}」が出やすい日。完璧を狙わず、ペースを落とすとうまくいきます。",
    "今日は「{kw}」のサイン。手放すこと・休むことが、明日の運気を上げます。",
]


def date_seed(date_str: str) -> int:
    """日付文字列から安定した整数シードを作る。"""
    h = hashlib.md5(date_str.encode("utf-8")).hexdigest()
    return int(h, 16)


def first_keyword(meaning: str) -> str:
    """「希望、理想、癒し」→「希望」のように先頭キーワードを取り出す。"""
    return meaning.replace("、", ",").split(",")[0].strip()


def pick_lucky_item(card: dict, rng: random.Random) -> str:
    if card["arcana"] == "major":
        candidates = config.LUCKY_ITEMS_BY_MAJOR.get(card["name"], config.LUCKY_ITEMS_DEFAULT)
    else:
        candidates = config.LUCKY_ITEMS_BY_SUIT.get(card["suit"], config.LUCKY_ITEMS_DEFAULT)
    return rng.choice(candidates)


def generate(date_str: str, major_only: bool = False) -> dict:
    """1枚引いて、投稿に必要な要素一式を組み立てて返す。"""
    rng = random.Random(date_seed(date_str + ("M" if major_only else "F")))

    if major_only:
        deck = [c for c in tarot_data.build_deck() if c["arcana"] == "major"]
    else:
        deck = tarot_data.build_deck()

    card = rng.choice(deck)
    is_upright = rng.random() < 0.5
    direction = "正位置" if is_upright else "逆位置"
    meaning = card["upright"] if is_upright else card["reverse"]
    kw = first_keyword(meaning)

    templates = UPRIGHT_TEMPLATES if is_upright else REVERSE_TEMPLATES
    message = rng.choice(templates).format(kw=kw)

    lucky_item = pick_lucky_item(card, rng)
    link = config.make_rakuten_link(lucky_item)

    return {
        "date": date_str,
        "card": card,
        "direction": direction,
        "is_upright": is_upright,
        "meaning": meaning,
        "message": message,
        "lucky_item": lucky_item,
        "link": link,
    }


def format_post_short(r: dict) -> str:
    """X / Bluesky 向けの短い投稿文。"""
    lines = []
    lines.append(f"🔮今日の1枚タロット🔮 {r['date']}")
    lines.append("")
    lines.append(f"「{r['card']['name']}」（{r['direction']}）")
    lines.append("")
    lines.append(r["message"])
    if config.ENABLE_AFFILIATE:
        lines.append("")
        lines.append(f"🍀ラッキーアイテム：{r['lucky_item']}")
        lines.append(r["link"])
    lines.append("")
    lines.append("#今日の占い #タロット #タロット占い #今日の1枚")
    return "\n".join(lines)


def format_post_note(r: dict) -> str:
    """note 向けの少し詳しい投稿文。"""
    lines = []
    lines.append(f"# 今日の1枚タロット（{r['date']}）")
    lines.append("")
    lines.append(f"今日のカードは **「{r['card']['name']}」（{r['direction']}）** です。")
    lines.append("")
    lines.append(f"このカードのキーワードは「{r['meaning']}」。")
    lines.append("")
    lines.append(r["message"])
    if config.ENABLE_AFFILIATE:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## 🍀今日のラッキーアイテム：{r['lucky_item']}")
        lines.append("")
        lines.append(f"運気を後押ししたい人はこちら → [{r['lucky_item']}を楽天で見る]({r['link']})")
    lines.append("")
    lines.append("#今日の占い #タロット #タロット占い")
    return "\n".join(lines)


def save_outputs(r: dict, short_text: str, note_text: str) -> str:
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"tarot_{r['date']}")
    with open(base + "_x.txt", "w", encoding="utf-8") as f:
        f.write(short_text)
    with open(base + "_note.md", "w", encoding="utf-8") as f:
        f.write(note_text)
    return out_dir


def main():
    parser = argparse.ArgumentParser(description="今日の1枚タロット投稿生成")
    parser.add_argument("--date", help="生成日 YYYY-MM-DD（省略時は今日）")
    parser.add_argument("--major", action="store_true", help="大アルカナのみから引く")
    parser.add_argument("--no-save", action="store_true", help="ファイル保存しない")
    args = parser.parse_args()

    date_str = args.date or datetime.date.today().isoformat()

    r = generate(date_str, major_only=args.major)
    short_text = format_post_short(r)
    note_text = format_post_note(r)

    print("=" * 50)
    print("【X / Bluesky 用】")
    print("=" * 50)
    print(short_text)
    print()
    print("=" * 50)
    print("【note 用】")
    print("=" * 50)
    print(note_text)

    if not args.no_save:
        out_dir = save_outputs(r, short_text, note_text)
        print()
        print(f"💾 保存先: {out_dir}")


if __name__ == "__main__":
    main()
