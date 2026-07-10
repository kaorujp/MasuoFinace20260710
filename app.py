import mysql.connector
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# データベースへの接続設定（本来はconfig.pyに隔離しますが、まずは分かりやすさ重視でここに集約）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # XAMPPのデフォルト
    "password": "",  # XAMPPのデフォルト
    "database": "masuo_db",
}


@app.route("/")
def index():
    # templates/index.html をブラウザに表示する役割
    return render_template("index.html")


@app.route("/api/sales", methods=["POST"])
def save_sales():
    """画面から送られてきた売上データを、安全にDBへ保存するバックエンド処理"""
    try:
        # 1. フロントエンド（画面）から送られてきたデータを受け取る
        data = request.json
        sales_date = data.get("date")
        hamburg_qty = int(data.get("hamburg_qty", 0))
        egg_qty = int(data.get("egg_qty", 0))
        utility_cost = int(data.get("utility_cost", 0))

        # 2. データベースに接続
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # ==========================================================
        # 🛡️ セキュリティ部門の鉄則：プレースホルダによるSQLインジェクション防御
        # ==========================================================
        # SQL文は「型」だけを定義し、値が入る場所は「%s」にしておく
        query = """
            INSERT INTO daily_sales (sales_date, hamburg_quantity, egg_quantity, utility_cost)
            VALUES (%s, %s, %s, %s)
        """
        # データは完全に「ただの数値・文字列」として別枠のタプルにする
        record_data = (sales_date, hamburg_qty, egg_qty, utility_cost)

        # 実行（データベース側で安全に文字の無害化処理が行われるため、ハッキングは100%不可能）
        cursor.execute(query, record_data)
        conn.commit()

        # 3. 簿記1級ロジック：自動利益計算（原価・家賃を引く）
        # ますおバーグ価格 1780円 - 肉原価200円 - その他10%(178円) = 1件あたりの粗利 1402円
        hamburg_profit = hamburg_qty * (1780 - 200 - 178)
        # エッグバーグ価格 1380円 - 肉原価200円 - その他10%(138円) = 1件あたりの粗利 1042円
        egg_profit = egg_qty * (1380 - 200 - 138)

        total_gross_profit = hamburg_profit + egg_profit
        fixed_cost_day = (600000 / 30) + (
            utility_cost / 30
        )  # 家賃と光熱費の「1日換算」

        net_profit_today = total_gross_profit - fixed_cost_day

        # 4. 接続を閉じて、安全にフロントエンドに結果を返す
        cursor.close()
        conn.close()

        return jsonify(
            {
                "status": "success",
                "message": "データを安全に保存しました（SQLインジェクション対策済）",
                "net_profit": int(net_profit_today),
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # サーバーを起動（ローカル環境）
    app.run(debug=True)