# 占いサイト自動運営ツール（集客フェーズ）

みみさんの稼働中エンジン／運用中Excelの計算ロジックを使い、
**人間の作業ゼロで毎日コンテンツを生成する**ツール群。

入っているのは2系統：

1. **今日の12星座占い（サイト用HTML）** ← `build_site.py`
2. **今日の1枚タロット（SNS投稿文）** ← `daily_tarot.py`

---

## A. 今日の12星座占い（4カテゴリ・パイプライン）

```
swisseph(惑星位置を自動計算) → zodiac_excel.compute_all(4カテゴリ) → 占いCSV(差し込み文) → HTML出力
```

各星座カードに **総合・仕事・恋愛・健康** の4運勢を、それぞれ本物のカテゴリ別
スコア(★1〜5)＋個別文面で表示。1星座4ブロック×12星座＝情報量の厚いページ。

**これまでExcelに手入力していた「月/水星/金星/火星/木星が今日いる星座」を
swissephで自動計算する**ので、人間の作業がゼロになった（= Excel手作業の解消）。

| ファイル | 役割 |
|---|---|
| `planets.py`     | swissephで今日の5天体の星座＋月相を自動計算（データファイル不要のMoshier使用） |
| `zodiac_excel.py`| 運用中Excelの総合運ランキング数式をPython移植（テスト一致済み） |
| `build_site.py`  | 上記を束ねて `output/index.html` を生成する本体 |

```powershell
python build_site.py                  # 今日のページを生成
python build_site.py --date 2026-06-10
python build_site.py --open           # 生成後ブラウザで開く
python planets.py 2026-06-03          # その日の惑星位置だけ確認
```

> 検証済み：2026-06-03 の swisseph 出力（月=やぎ座/水星=かに座/金星=かに座/火星=おうし座/木星=かに座）は
> みみさんが Excel に手入力していた値・zodiac_excel のテストケースと完全一致する。
> 4カテゴリのスコアも zodiac_excel のテスト正解（おうし座 総合4/仕事3/恋愛3/健康5 …）と全一致。

---

## B. 今日の1枚タロット（SNS投稿文）

X / Bluesky / note にコピペできる投稿文を自動生成。

| ファイル | 役割 |
|---|---|
| `daily_tarot.py` | 本体。実行するとその日の投稿文を生成 |
| `tarot_data.py`  | カード意味データ（大アルカナ22＋小アルカナ56）。Tarotエンジンから移植 |
| `config.py`      | 楽天アフィリID・ラッキーアイテム候補の設定（A/B共用） |
| `output/`        | 生成物（HTML / 投稿文 .txt / .md） |

> ⚠️ 既存ツール `C:\pleiades\2023-09\workspace\Tarot` / `FortunePromptMaker` には一切触れていません。
> 意味データ・数式をコピー／移植しただけです。占いCSV（`C:\Users\y5268\Desktop\占い`）も読むだけ。

---

## 使い方

```powershell
cd C:\Users\y5268\Desktop\kaihatu\hukugyou
python daily_tarot.py                  # 今日の1枚を生成して output/ に保存
python daily_tarot.py --date 2026-06-10  # 日付を指定
python daily_tarot.py --major          # 大アルカナ22枚のみから引く
python daily_tarot.py --no-save        # 画面表示のみ（保存しない）
```

- **日付シード方式**：同じ日に何度実行しても同じカードが出ます（投稿のブレ防止）。
- 出力は `output/` に X用(.txt)とnote用(.md)の2種類が保存されます。

---

## 楽天アフィリエイトの設定（後付けOK）

1. 楽天アフィリエイトに登録 → アフィリエイトIDを取得
2. `config.py` の `RAKUTEN_AFFILIATE_ID = ""` にIDを記入
3. これだけで、投稿内のリンクがアフィリリンクに切り替わります

> 登録前でも `ENABLE_AFFILIATE = True` なら「楽天で検索」リンクが入ります。
> 占い部分だけ先に投稿運用したいなら `ENABLE_AFFILIATE = False` に。

ラッキーアイテムの商品キーワードも `config.py` で自由に編集できます。

---

## 次の一手（案）

- [x] **惑星位置の自動計算**：swissephでExcel手入力を解消（`planets.py`）✅
- [x] **最小構成パイプライン**：CSV→ランキング→HTML を無人で通す（`build_site.py`）✅
- [x] **カテゴリ別運勢**：総合/仕事/恋愛/健康の4カテゴリをHTML表示（`compute_all`連携）✅
- [ ] **毎日自動実行**：Windowsタスクスケジューラで `python build_site.py` を毎朝0時に実行
- [ ] **月相補正**：今は月相を「表示」のみ。月相版CSVデータを投入してスコアに反映（差別化の本丸）
- [ ] **個別ページ量産**：「おうし座の今日の運勢」等を星座×日付で自動生成し内部リンクで束ねる
- [ ] **公開先**：GitHub Pages / Netlify など（静的HTMLなので無料で置ける）
- [ ] **ココナラ導線**：ページ末に「本格鑑定はこちら」（FortunePromptMaker鑑定へ）
