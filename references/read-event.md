# イベントを 読む 手順（書く まえに 文脈を そろえる）

novel2agent-jp の「書く まえに 文脈パックを 作り、それだけを 見て 書く」を、地図の 台本むけに した もの。
読んだ 結果は 下の「場面メモ」の 形で 書き出し、それを 見ながら 書く。

**主人公の 家（data/maps/PalletTown_PlayersHouse_*）の 台本は ユーザーの ゆるし なく 開かない。**

## 1. 対象の 地図を 読む

1. `data/maps/<地図>/scripts.inc` の 先頭の `@` の 注を 読む（場面の 流れ・旗・仮の 台詞か どうかが 書いて ある）
2. `MapScripts`（ON_TRANSITION / ON_FRAME / ON_WARP_INTO_MAP_TABLE）で、人を 出す 旗と 場面の 始まりの 条件を 見る
3. 場面の スクリプトを 上から 読み、次を 順に 書き出す
   - だれが（LOCALID と 見た目）、どこで（座標）、何を するか（msgbox・applymovement・trainerbattle・giveitem…）
   - 旗と 変数の 条件（goto_if_set / goto_if_eq / setflag / setvar）
   - その 場面で 出る 台詞の ラベル（msgbox / trainerbattle の 引数 / pokenavcall）
4. `data/maps/<地図>/map.json` で
   - object_events: local_id・graphics_id（名札が 自動で 出る 見た目か）・x,y・flag（出し入れ）・script
   - coord_events: 踏むと 始まる マスと var / var_value
   - bg_events: 看板
5. 人を 動かす・置く ときは、通れる マス（layout の map.bin）と 画面で たしかめる。向きは ON_WARP の `turnobject`、足踏みの 命令（WalkInPlace）は 使わない（メモ event-placement-check）

## 2. 前後の イベントを 読む

1. 出る 人物の 名前で さがす（主人公の 家は のぞく）:
   `grep -rl --exclude-dir='PalletTown_PlayersHouse*' "ナナミ『" data/maps data/scripts data/text`
   （家の フォルダは grep の 段階で 外す。あとから grep -v で 消す 書き方は 使わない）
2. 同じ 人物の 直前と 直後の イベント（バッジの 順・旗の 順）の 台詞を 読み、
   - その 時点で 人物が 何を 知って いて 何を 知らないか（novel2agent の 知識状態チェック）
   - 前の 場面で 約束・予告した こと（「3びきは かならず とりかえそう」など）
   - 呼び方・語尾が characters/*.toml と 合って いるか
3. facts.toml と くいちがう ことが ないか 見る
4. 公式に 同じ 種類の 場面が あれば、その 台詞を 読む（`scripts/find_official.py --kind 勝負のまえ --map <地図>` など）。
   改造の 地図でも 英文の まま の ラベルは ビルドで 公式の 日本語に なるので、まわりの 公式の 台詞と 口調を そろえる
5. デバッグの イベントテスト（data/scripts/debug_event_jump.inc）の 注に、イベントの 順と 前提が まとまって いる

## 3. 場面メモ（書き出す 形）

```
場面: 9ばんどうろ 岸の はし / なみのりを もらった あと（FLAG_FOUGHT_ARTICUNO が 立って いない）
出る 人: ナナミ（FLAG_TEMP_2 で 出す）・主人公
直前: てんき けんきゅうじょで アテナを おいはらった（ナナミは その 場に いない）
直後: アテナ・したっぱ・フリーザーの 場面
ナナミが 知って いる こと: ロケットだんが 9ばんに いる / 知らない こと: フリーザーの オーラが きえる こと
台詞の ラベル: Route9_Text_…（新しく 作る ものは ここに 名前を 書く）
窓: ふつう（msgbox）／ 電話（pokenavcall）
```

このメモと characters/*.toml・facts.toml だけを 見て 書く。メモに ない 事実を 台詞で 作らない（作るなら facts.toml に proposed で 足して ユーザーに きく）。
