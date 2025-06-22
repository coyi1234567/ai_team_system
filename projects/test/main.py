#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目 - 主服务
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    """首页"""
    return jsonify({
        "message": "测试项目API服务",
        "version": "1.0.0",
        "status": "running"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True) 