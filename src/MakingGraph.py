import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


# CSVファイルのパス
file_path = r"\2024-01-28_gps.csv"
df = pd.read_csv(file_path)
print(df.head())  # 確認
plt.rcParams["font.family"] = "MS Gothic"  # フォント


# 基準点の緯度と経度
base_lat, base_lon = 33.84819047811515, 132.77103016377987
X_label = "RSSI"
X_label_unit = "/dBm"
Y_label = "SNR"
Y_label_unit = "/dB"

Ard_diff_sec = 0  # ardのプログラムミスでUTCなので9時間ずらす
start_sec = 72060
end_sec = 73400


# 2点間の距離計算
def haversine(lat1, lon1, lat2, lon2):
    # 地球の半径（キロメートル）
    R = 6371.0
    # 緯度経度をラジアンに変換
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    # 緯度と経度の差
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # ハーバーサイン公式
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    # 距離
    distance = R * c * 1000
    return distance


# 時間計算
df["時間"] = df["hour"] * 3600 + df["min"] * 60 + df["sec"]
df.loc[df["device_name"] == "No3_ARDLA66", "時間"] -= Ard_diff_sec

# 特定の時間範囲でフィルタリング（0秒から1160秒）
df = df[(df["時間"] >= start_sec) & (df["時間"] <= end_sec)]

# 距離の計算
df["距離"] = df.apply(lambda row: haversine(base_lat, base_lon, row["latitude"], row["longitude"]), axis=1)
print(df["距離"])


# device_nameごとにグループ化
grouped = df.groupby("device_name")

# 新しい図を作成
plt.figure(figsize=(10, 6))

# 各グループに対して散布図をプロット
for name, group in grouped:
    plt.scatter(group[X_label], group[Y_label], label=name)


# 近似曲線追加
"""
for name, group in grouped:
    x_values = group[X_label].values.reshape(-1, 1)
    y_values = group[Y_label].values
    model = LinearRegression().fit(np.log(x_values), y_values)  # 対数変換して線形フィット
    # プロット用の x 値を生成（範囲を広げる）
    x_range = np.logspace(np.log10(group[X_label].min()), np.log10(group[X_label].max()) + 1.6, 100)
    y_range = model.predict(np.log(x_range.reshape(-1, 1)))

    # プロット
    plt.plot(x_range, y_range, linestyle="--")
"""

# タイトルと軸のラベルを設定
# plt.title(f"{X_label}と{Y_label}の関係")
plt.xlabel(X_label + X_label_unit, fontsize=15)
plt.ylabel(Y_label + Y_label_unit, fontsize=15)
# plt.xlim([1, 1000])  # X軸の範囲を設定
plt.ylim([0, 18])  # Y軸の範囲を設定
# plt.ylim([最小値, 最大値]): #Y軸の範囲を設定

plt.grid(True)  # グリッド表示
plt.legend(loc="best", fontsize=15)  # 凡例を表示
# plt.xscale("log")
# plt.yscale("log")

# グラフを表示
plt.show()


"""
基本設定
タイトルと軸ラベル:
plt.title('タイトル'): グラフのタイトルを設定。
plt.xlabel('X軸のラベル'): X軸のラベルを設定。
plt.ylabel('Y軸のラベル'): Y軸のラベルを設定。
軸の範囲:
plt.xlim([最小値, 最大値]): X軸の範囲を設定。
plt.ylim([最小値, 最大値]): Y軸の範囲を設定。
軸のスケール:
plt.xscale('log'): X軸を対数スケールに設定。
plt.yscale('log'): Y軸を対数スケールに設定。
グリッドの表示:
plt.grid(True): グリッドを表示。
凡例の表示:
plt.legend(['ラベル1', 'ラベル2', ...]): 凡例を表示。
図のサイズ:
plt.figure(figsize=(幅, 高さ)): 図のサイズを設定。
散布図固有の設定
マーカーのスタイル:
plt.scatter(x, y, marker='o'): マーカーの形を設定（例: 'o', 's', '^'）。
マーカーのサイズと色:
plt.scatter(x, y, s=サイズ, color='色'): マーカーのサイズと色を設定。
透明度:
plt.scatter(x, y, alpha=透明度): マーカーの透明度を設定（0から1の間の値）。
線グラフ固有の設定
線のスタイルと色:
plt.plot(x, y, linestyle='--', color='色'): 線のスタイルと色を設定。
線の幅:
plt.plot(x, y, linewidth=幅): 線の幅を設定。
ヒストグラム固有の設定
ビンの数と範囲:
plt.hist(x, bins=ビンの数, range=[最小値, 最大値]): ヒストグラムのビンの数と範囲を設定。
その他のカスタマイズ
フォントサイズ:
plt.title('タイトル', fontsize=サイズ): タイトルのフォントサイズを設定。
同様に、軸ラベルや凡例のフォントサイズも設定可能。
軸の目盛り:
plt.xticks([目盛りのリスト]): X軸の目盛りをカスタマイズ。
plt.yticks([目盛りのリスト]): Y軸の目盛りをカスタマイズ。
軸の目盛りラベル:
plt.xticks([目盛りのリスト], [ラベルのリスト]): X軸の目盛りラベルをカスタマイズ。
plt.yticks([目盛りのリスト], [ラベルのリスト]): Y軸の目盛りラベルをカスタマイズ。
    

"""
