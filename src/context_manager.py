import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import os
from datetime import datetime

class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = 1    # 关键信息：项目需求、核心决策
    HIGH = 2        # 重要信息：技术方案、架构设计
    MEDIUM = 3      # 一般信息：实现细节、配置
    LOW = 4         # 次要信息：日志、临时数据

class ContextType(Enum):
    """上下文类型"""
    REQUIREMENT = "requirement"      # 需求信息
    DESIGN = "design"               # 设计信息
    IMPLEMENTATION = "implementation" # 实现信息
    CONFIGURATION = "configuration"  # 配置信息
    LOG = "log"                     # 日志信息
    TEMP = "temp"                   # 临时信息

@dataclass
class ContextItem:
    """上下文项"""
    key: str
    value: Any
    priority: ContextPriority
    context_type: ContextType
    stage: str
    timestamp: float
    hash: str = field(init=False)
    size: int = field(init=False)
    
    def __post_init__(self):
        self.hash = self._calculate_hash()
        self.size = self._calculate_size()
    
    def _calculate_hash(self) -> str:
        """计算内容的哈希值，用于去重"""
        content = f"{self.key}:{str(self.value)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _calculate_size(self) -> int:
        """估算内容大小（字符数）"""
        return len(str(self.value))

class SmartContextManager:
    """智能上下文管理器"""
    
    def __init__(self, project_dir: str, max_context_size: int = 8000):
        self.project_dir = project_dir
        self.max_context_size = max_context_size
        self.context_items: Dict[str, ContextItem] = {}
        self.context_cache: Dict[str, str] = {}
        self.stage_dependencies: Dict[str, List[str]] = {
            "requirement_analysis": [],
            "technical_design": ["requirement_analysis"],
            "ui_design": ["requirement_analysis", "technical_design"],
            "frontend_development": ["requirement_analysis", "technical_design", "ui_design"],
            "backend_development": ["requirement_analysis", "technical_design"],
            "data_analysis": ["requirement_analysis", "technical_design"],
            "testing": ["frontend_development", "backend_development"],
            "deployment": ["frontend_development", "backend_development", "testing"],
            "documentation": ["requirement_analysis", "technical_design", "frontend_development", "backend_development"],
            "acceptance": ["testing", "deployment", "documentation"]
        }
        
        # 加载持久化的上下文
        self._load_persistent_context()
    
    def add_context(self, key: str, value: Any, priority: ContextPriority, 
                   context_type: ContextType, stage: str) -> None:
        """添加上下文项"""
        item = ContextItem(
            key=key,
            value=value,
            priority=priority,
            context_type=context_type,
            stage=stage,
            timestamp=datetime.now().timestamp()
        )
        
        # 检查是否已存在相同内容
        if item.hash in [existing.hash for existing in self.context_items.values()]:
            print(f"[上下文管理] 检测到重复内容，跳过: {key}")
            return
        
        self.context_items[key] = item
        self._save_persistent_context()
        print(f"[上下文管理] 添加上下文: {key} (优先级:{priority.name}, 类型:{context_type.value})")
    
    def get_context_for_stage(self, stage: str, agent_role: Optional[str] = None) -> str:
        """为指定阶段生成优化的上下文"""
        cache_key = f"{stage}_{agent_role}"
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        # 获取依赖阶段
        dependencies = self.stage_dependencies.get(stage, [])
        
        # 根据阶段和角色选择相关上下文
        relevant_items = self._select_relevant_items(stage, agent_role, dependencies)
        
        # 生成结构化上下文
        context_str = self._generate_structured_context(relevant_items, stage, agent_role)
        
        # 缓存结果
        self.context_cache[cache_key] = context_str
        return context_str
    
    def _select_relevant_items(self, stage: str, agent_role: Optional[str], dependencies: List[str]) -> List[ContextItem]:
        """选择相关的上下文项"""
        relevant_items = []
        
        for item in self.context_items.values():
            # 1. 检查阶段依赖
            if item.stage in dependencies or item.stage == stage:
                relevant_items.append(item)
                continue
            
            # 2. 根据角色选择特定类型的内容
            if agent_role:
                if self._is_role_relevant(item, agent_role):
                    relevant_items.append(item)
                    continue
            
            # 3. 始终包含关键信息
            if item.priority == ContextPriority.CRITICAL:
                relevant_items.append(item)
                continue
        
        # 按优先级和大小排序
        relevant_items.sort(key=lambda x: (x.priority.value, x.size))
        
        # 控制总大小
        total_size = 0
        selected_items = []
        for item in relevant_items:
            if total_size + item.size <= self.max_context_size:
                selected_items.append(item)
                total_size += item.size
            else:
                break
        
        return selected_items
    
    def _is_role_relevant(self, item: ContextItem, agent_role: str) -> bool:
        """判断上下文项是否与角色相关"""
        role_context_map = {
            "product_manager": [ContextType.REQUIREMENT, ContextType.DESIGN],
            "tech_lead": [ContextType.DESIGN, ContextType.IMPLEMENTATION],
            "frontend_dev": [ContextType.IMPLEMENTATION, ContextType.CONFIGURATION],
            "backend_dev": [ContextType.IMPLEMENTATION, ContextType.CONFIGURATION],
            "ui_designer": [ContextType.DESIGN],
            "qa_engineer": [ContextType.IMPLEMENTATION],
            "devops_engineer": [ContextType.CONFIGURATION],
            "data_analyst": [ContextType.REQUIREMENT, ContextType.IMPLEMENTATION],
            "boss": [ContextType.REQUIREMENT]
        }
        
        relevant_types = role_context_map.get(agent_role, [])
        return item.context_type in relevant_types
    
    def _generate_structured_context(self, items: List[ContextItem], stage: str, agent_role: Optional[str]) -> str:
        """生成结构化的上下文字符串"""
        if not items:
            return "无相关上下文信息"
        
        # 按类型分组
        grouped_items = {}
        for item in items:
            if item.context_type not in grouped_items:
                grouped_items[item.context_type] = []
            grouped_items[item.context_type].append(item)
        
        # 生成结构化内容
        context_parts = []
        context_parts.append(f"=== 项目上下文 (阶段: {stage}, 角色: {agent_role}) ===\n")
        
        # 1. 关键信息（始终在最前面）
        critical_items = [item for item in items if item.priority == ContextPriority.CRITICAL]
        if critical_items:
            context_parts.append("【关键信息】")
            for item in critical_items:
                context_parts.append(f"• {item.key}: {self._compress_value(item.value)}")
            context_parts.append("")
        
        # 2. 按类型组织其他信息
        type_names = {
            ContextType.REQUIREMENT: "需求信息",
            ContextType.DESIGN: "设计信息", 
            ContextType.IMPLEMENTATION: "实现信息",
            ContextType.CONFIGURATION: "配置信息",
            ContextType.LOG: "日志信息"
        }
        
        for context_type, type_items in grouped_items.items():
            if context_type == ContextType.TEMP:  # 跳过临时信息
                continue
                
            context_parts.append(f"【{type_names.get(context_type, context_type.value)}】")
            for item in type_items:
                if item.priority != ContextPriority.CRITICAL:  # 避免重复
                    context_parts.append(f"• {item.key}: {self._compress_value(item.value)}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _compress_value(self, value: Any) -> str:
        """压缩值，减少Token使用"""
        if isinstance(value, str):
            # 如果字符串太长，进行摘要
            if len(value) > 500:
                # 提取关键信息
                lines = value.split('\n')
                if len(lines) > 10:
                    summary_lines = lines[:5] + ["..."] + lines[-5:]
                    return "\n".join(summary_lines)
                else:
                    return value[:500] + "..." if len(value) > 500 else value
            return value
        elif isinstance(value, dict):
            # 只保留关键字段
            key_fields = ['requirements', 'project_name', 'stage', 'result']
            compressed = {}
            for key in key_fields:
                if key in value:
                    compressed[key] = self._compress_value(value[key])
            return str(compressed)
        else:
            return str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
    
    def clear_cache(self) -> None:
        """清除上下文缓存"""
        self.context_cache.clear()
    
    def get_context_stats(self) -> Dict[str, Any]:
        """获取上下文统计信息"""
        stats = {
            "total_items": len(self.context_items),
            "total_size": sum(item.size for item in self.context_items.values()),
            "by_priority": {},
            "by_type": {},
            "by_stage": {}
        }
        
        for item in self.context_items.values():
            # 按优先级统计
            priority_name = item.priority.name
            if priority_name not in stats["by_priority"]:
                stats["by_priority"][priority_name] = {"count": 0, "size": 0}
            stats["by_priority"][priority_name]["count"] += 1
            stats["by_priority"][priority_name]["size"] += item.size
            
            # 按类型统计
            type_name = item.context_type.value
            if type_name not in stats["by_type"]:
                stats["by_type"][type_name] = {"count": 0, "size": 0}
            stats["by_type"][type_name]["count"] += 1
            stats["by_type"][type_name]["size"] += item.size
            
            # 按阶段统计
            if item.stage not in stats["by_stage"]:
                stats["by_stage"][item.stage] = {"count": 0, "size": 0}
            stats["by_stage"][item.stage]["count"] += 1
            stats["by_stage"][item.stage]["size"] += item.size
        
        return stats
    
    def _save_persistent_context(self) -> None:
        """保存上下文到文件"""
        try:
            context_file = os.path.join(self.project_dir, 'smart_context.json')
            data = {
                "items": {
                    key: {
                        "key": item.key,
                        "value": item.value,
                        "priority": item.priority.value,
                        "context_type": item.context_type.value,
                        "stage": item.stage,
                        "timestamp": item.timestamp,
                        "hash": item.hash,
                        "size": item.size
                    }
                    for key, item in self.context_items.items()
                }
            }
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[上下文管理] 保存上下文失败: {e}")
    
    def _load_persistent_context(self) -> None:
        """从文件加载上下文"""
        try:
            context_file = os.path.join(self.project_dir, 'smart_context.json')
            if os.path.exists(context_file):
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key, item_data in data.get("items", {}).items():
                    item = ContextItem(
                        key=item_data["key"],
                        value=item_data["value"],
                        priority=ContextPriority(item_data["priority"]),
                        context_type=ContextType(item_data["context_type"]),
                        stage=item_data["stage"],
                        timestamp=item_data["timestamp"]
                    )
                    self.context_items[key] = item
                
                print(f"[上下文管理] 加载了 {len(self.context_items)} 个上下文项")
        except Exception as e:
            print(f"[上下文管理] 加载上下文失败: {e}")
    
    def cleanup_old_context(self, max_age_hours: int = 24) -> None:
        """清理过期的上下文"""
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        items_to_remove = []
        for key, item in self.context_items.items():
            if current_time - item.timestamp > max_age_seconds:
                items_to_remove.append(key)
        
        for key in items_to_remove:
            del self.context_items[key]
        
        if items_to_remove:
            print(f"[上下文管理] 清理了 {len(items_to_remove)} 个过期上下文项")
            self._save_persistent_context()
            self.clear_cache() 