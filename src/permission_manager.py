#!/usr/bin/env python3
"""
本地RBAC+ABAC权限管理模块
- 支持用户、角色、资源、操作、优先级判定
- 权限表本地json存储，便于扩展
"""
import json
from pathlib import Path
from typing import Optional, List, Dict

PERMISSION_FILE = Path(__file__).parent.parent / "config/permissions.json"

class PermissionManager:
    def __init__(self, permission_file: Path = PERMISSION_FILE):
        self.permission_file = permission_file
        self.permissions = self._load_permissions()

    def _load_permissions(self) -> List[Dict]:
        if self.permission_file.exists():
            with open(self.permission_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_permissions(self):
        with open(self.permission_file, "w", encoding="utf-8") as f:
            json.dump(self.permissions, f, ensure_ascii=False, indent=2)

    def add_permission(self, user_id: Optional[str], role: Optional[str], resource_type: str, resource_id: str, action: str, allow: bool, note: str = ""):
        """添加权限，user_id/role 二选一，allow=True为允许，False为拒绝"""
        self.permissions.append({
            "user_id": user_id,
            "role": role,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "allow": allow,
            "note": note
        })
        self.save_permissions()

    def has_permission(self, user_id: str, role: str, resource_type: str, resource_id: str, action: str) -> bool:
        """
        权限判定优先级：
        1. 个人特批（user_id）
        2. 角色权限（role）
        3. 默认拒绝
        """
        # 1. 查个人权限
        for p in self.permissions:
            if p["user_id"] == user_id and p["resource_type"] == resource_type and p["resource_id"] == resource_id and p["action"] == action:
                return p["allow"]
        # 2. 查角色权限
        for p in self.permissions:
            if p["role"] == role and p["resource_type"] == resource_type and p["resource_id"] == resource_id and p["action"] == action:
                return p["allow"]
        # 3. 默认拒绝
        return False

    def list_permissions(self, user_id: Optional[str] = None, role: Optional[str] = None) -> List[Dict]:
        """列出某用户或角色的所有权限"""
        result = []
        for p in self.permissions:
            if (user_id and p["user_id"] == user_id) or (role and p["role"] == role):
                result.append(p)
        return result

# 示例用法
if __name__ == "__main__":
    pm = PermissionManager()
    # 添加角色权限
    pm.add_permission(user_id=None, role="boss", resource_type="doc", resource_id="d123", action="read", allow=True, note="boss可读d123")
    pm.add_permission(user_id=None, role="dev", resource_type="doc", resource_id="d123", action="read", allow=False, note="dev禁止读d123")
    # 添加个人特批
    pm.add_permission(user_id="u001", role=None, resource_type="doc", resource_id="d123", action="read", allow=True, note="u001特批可读d123")
    # 权限判定
    print("u001 boss:", pm.has_permission("u001", "boss", "doc", "d123", "read"))  # True（个人特批）
    print("u002 dev:", pm.has_permission("u002", "dev", "doc", "d123", "read"))    # False（角色禁止）
    print("u003 boss:", pm.has_permission("u003", "boss", "doc", "d123", "read"))  # True（角色允许）
    print("u004 dev:", pm.has_permission("u004", "dev", "doc", "d123", "read"))    # False（角色禁止）
    print("u005 pm:", pm.has_permission("u005", "pm", "doc", "d123", "read"))      # False（无权限） 