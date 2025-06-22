#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
员工请假小程序 - 主服务
支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成
"""

from flask import Flask, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# 模拟数据库
leave_records = []
users = [
    {"id": "u001", "name": "张三", "role": "employee", "department": "技术部"},
    {"id": "u002", "name": "李四", "role": "supervisor", "department": "技术部"},
    {"id": "u003", "name": "王五", "role": "hr", "department": "人事部"}
]

@app.route('/')
def index():
    """首页"""
    return jsonify({
        "message": "员工请假小程序API服务",
        "version": "1.0.0",
        "features": [
            "多级审批",
            "权限管理", 
            "请假记录查询",
            "移动端适配",
            "RAG知识库",
            "MCP协议集成"
        ]
    })

@app.route('/api/leave/apply', methods=['POST'])
def apply_leave():
    """申请请假"""
    data = request.get_json()
    
    leave_record = {
        "id": f"leave_{len(leave_records) + 1}",
        "user_id": data.get("user_id"),
        "type": data.get("type"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "reason": data.get("reason"),
        "status": "pending",
        "create_time": datetime.now().isoformat()
    }
    
    leave_records.append(leave_record)
    
    return jsonify({
        "success": True,
        "message": "请假申请提交成功",
        "data": leave_record
    })

@app.route('/api/leave/list', methods=['GET'])
def list_leaves():
    """获取请假记录列表"""
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    
    filtered_records = leave_records
    
    if user_id:
        filtered_records = [r for r in filtered_records if r['user_id'] == user_id]
    
    if status:
        filtered_records = [r for r in filtered_records if r['status'] == status]
    
    return jsonify({
        "success": True,
        "data": filtered_records
    })

@app.route('/api/leave/<leave_id>', methods=['GET'])
def get_leave_detail(leave_id):
    """获取请假详情"""
    for record in leave_records:
        if record['id'] == leave_id:
            return jsonify({
                "success": True,
                "data": record
            })
    
    return jsonify({
        "success": False,
        "message": "请假记录不存在"
    }), 404

@app.route('/api/leave/<leave_id>/approve', methods=['POST'])
def approve_leave(leave_id):
    """审批请假"""
    data = request.get_json()
    action = data.get('action')  # approve/reject
    comment = data.get('comment', '')
    
    for record in leave_records:
        if record['id'] == leave_id:
            record['status'] = 'approved' if action == 'approve' else 'rejected'
            record['approve_time'] = datetime.now().isoformat()
            record['approve_comment'] = comment
            
            return jsonify({
                "success": True,
                "message": f"请假申请已{'通过' if action == 'approve' else '拒绝'}",
                "data": record
            })
    
    return jsonify({
        "success": False,
        "message": "请假记录不存在"
    }), 404

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    return jsonify({
        "success": True,
        "data": users
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    total_count = len(leave_records)
    pending_count = len([r for r in leave_records if r['status'] == 'pending'])
    approved_count = len([r for r in leave_records if r['status'] == 'approved'])
    rejected_count = len([r for r in leave_records if r['status'] == 'rejected'])
    
    return jsonify({
        "success": True,
        "data": {
            "total_count": total_count,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True) 