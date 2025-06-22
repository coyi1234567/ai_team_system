#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测序业务项目 - 主服务
"""

from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# 模拟数据库
sequencing_jobs = []

@app.route('/')
def index():
    return jsonify({
        "message": "测序业务API服务",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/api/job/submit', methods=['POST'])
def submit_job():
    data = request.get_json()
    job = {
        "id": f"job_{len(sequencing_jobs) + 1}",
        "sample_name": data.get("sample_name"),
        "sequencing_type": data.get("sequencing_type"),
        "status": "pending",
        "submit_time": datetime.now().isoformat()
    }
    sequencing_jobs.append(job)
    return jsonify({"success": True, "message": "测序任务提交成功", "data": job})

@app.route('/api/job/list', methods=['GET'])
def list_jobs():
    return jsonify({"success": True, "data": sequencing_jobs})

@app.route('/api/job/<job_id>', methods=['GET'])
def get_job(job_id):
    for job in sequencing_jobs:
        if job['id'] == job_id:
            return jsonify({"success": True, "data": job})
    return jsonify({"success": False, "message": "任务不存在"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True) 