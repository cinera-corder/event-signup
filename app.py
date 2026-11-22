import threading
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

CAPACITY = 10          # 정원 (시연용으로 3으로 낮춰도 됨)
applicants = {}        # {학번: 이름} 서버 메모리 저장
lock = threading.Lock()  # 동시에 신청이 들어와도 정원이 안 깨지게 함


def snapshot():
    return {
        "capacity": CAPACITY,
        "remaining": CAPACITY - len(applicants),
        "applicants": [{"student_id": s, "name": n} for s, n in applicants.items()],
    }


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/list")
def list_applicants():
    with lock:
        return jsonify(snapshot())


@app.post("/api/apply")
def apply_event():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    sid = str(data.get("student_id", "")).strip()
    if not name or not sid:
        return jsonify(error="이름과 학번을 모두 입력해 주세요."), 400
    if len(name) > 20 or not sid.isdigit() or not 8 <= len(sid) <= 10:
        return jsonify(error="학번은 숫자 8~10자리, 이름은 20자 이하로 입력해 주세요."), 400
    with lock:
        if sid in applicants:
            return jsonify(error="이미 신청된 학번입니다."), 409
        if len(applicants) >= CAPACITY:
            return jsonify(error="정원이 마감되었습니다."), 409
        applicants[sid] = name
        return jsonify(message="신청이 완료되었습니다.", **snapshot()), 201


@app.post("/api/cancel")
def cancel_event():
    data = request.get_json(silent=True) or {}
    sid = str(data.get("student_id", "")).strip()
    if not sid:
        return jsonify(error="학번을 입력해 주세요."), 400
    with lock:
        if sid not in applicants:
            return jsonify(error="신청 내역이 없는 학번입니다."), 404
        del applicants[sid]
        return jsonify(message="신청이 취소되었습니다.", **snapshot())