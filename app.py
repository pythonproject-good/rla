from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

DATA_FILE = "data.json"

# 데이터 파일 초기화
if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
    with open(DATA_FILE, 'w') as f:
        json.dump({"passwords": {}, "company_balance": 0, "notices": []}, f)


# 데이터 불러오기
def load_data():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    # 기본값 설정: 키가 없으면 자동으로 추가
    if "company_balance" not in data:
        data["company_balance"] = 0
    if "passwords" not in data:
        data["passwords"] = {}
    if "notices" not in data:
        data["notices"] = []

    save_data(data)  # 기본값이 추가된 데이터를 다시 저장
    return data


# 데이터 저장하기
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# --------- 로그인 페이지 ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        input_password = request.form.get("password")
        data = load_data()
        if input_password in data["passwords"]:
            session["password"] = input_password
            return redirect(url_for("user_page"))
        else:
            return render_template("login.html", error="유효하지 않은 비밀번호입니다.")
    return render_template("login.html")


# --------- 사용자 페이지 ----------
@app.route("/user", methods=["GET", "POST"])
def user_page():
    if "password" not in session:
        return redirect(url_for("login"))
    data = load_data()
    password = session["password"]
    user_data = data["passwords"].get(password, {})

    if request.method == "POST" and user_data.get("can_write_notice"):
        new_notice = request.form.get("notice")
        data["notices"].append({"notice": new_notice, "comments": []})
        save_data(data)
        return redirect(url_for("user_page"))

    return render_template("user_notice.html",
                           can_write_notice=user_data.get("can_write_notice", False),
                           balance=data["company_balance"],
                           notices=data["notices"])


# --------- 댓글 작성 ----------
@app.route("/comment/<int:notice_id>", methods=["POST"])
def comment(notice_id):
    if "password" not in session:
        return redirect(url_for("login"))

    comment_text = request.form.get("comment")
    data = load_data()

    if 0 <= notice_id < len(data["notices"]):
        data["notices"][notice_id]["comments"].append(comment_text)
        save_data(data)
    return redirect(url_for("user_page"))


# --------- 관리자 페이지 ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    data = load_data()
    if request.method == "POST":
        action = request.form.get("action")

        # 비밀번호 발급
        if action == "add_user":
            new_password = request.form.get("new_password")
            can_write_notice = request.form.get("can_write_notice") == "yes"
            data["passwords"][new_password] = {"can_write_notice": can_write_notice}

        # 비밀번호 삭제
        elif action == "delete_user":
            delete_password = request.form.get("delete_password")
            data["passwords"].pop(delete_password, None)

        # 회사 잔액 수정
        elif action == "update_balance":
            balance = request.form.get("balance", type=int)
            data["company_balance"] = balance

        save_data(data)
    return render_template("admin.html", users=data["passwords"], balance=data["company_balance"])


# --------- 로그아웃 ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------- 애플리케이션 실행 ----------
if __name__ == "__main__":
    app.run(debug=True)
