#!/usr/bin/env python3
"""
智能上下文管理器测试脚本
验证Token节省效果和上下文优化功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.context_manager import SmartContextManager, ContextPriority, ContextType

def test_context_manager():
    """测试智能上下文管理器"""
    print("=== 智能上下文管理器测试 ===\n")
    
    # 创建测试项目目录
    test_project_dir = "test_context_project"
    os.makedirs(test_project_dir, exist_ok=True)
    
    # 初始化上下文管理器
    context_manager = SmartContextManager(test_project_dir, max_context_size=5000)
    
    # 模拟项目各阶段的数据
    test_data = {
        "project_requirements": "开发一个员工请假小程序，支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成、自动化部署。" * 10,  # 重复10次模拟长文本
        "requirement_analysis_result": "需求分析结果：经过详细分析，项目需要包含以下核心功能..." * 15,
        "technical_design_result": "技术设计方案：采用前后端分离架构，前端使用React，后端使用Python Flask..." * 20,
        "ui_design_result": "UI设计方案：采用现代化设计风格，主色调为蓝色，布局简洁明了..." * 12,
        "frontend_development_result": "前端开发方案：使用React + TypeScript，组件化开发，响应式设计..." * 18,
        "backend_development_result": "后端开发方案：使用Python Flask + SQLAlchemy，RESTful API设计..." * 16,
        "testing_result": "测试方案：单元测试覆盖率90%，集成测试，端到端测试..." * 8,
        "deployment_result": "部署方案：使用Docker容器化部署，支持CI/CD流水线..." * 10
    }
    
    # 添加测试数据到上下文管理器
    print("1. 添加测试数据到上下文管理器...")
    for key, value in test_data.items():
        if "requirement" in key:
            priority = ContextPriority.CRITICAL
            context_type = ContextType.REQUIREMENT
        elif "design" in key:
            priority = ContextPriority.HIGH
            context_type = ContextType.DESIGN
        elif "development" in key:
            priority = ContextPriority.HIGH
            context_type = ContextType.IMPLEMENTATION
        else:
            priority = ContextPriority.MEDIUM
            context_type = ContextType.IMPLEMENTATION
        
        stage = key.replace("_result", "").replace("project_", "")
        context_manager.add_context(key, value, priority, context_type, stage)
    
    print(f"   添加了 {len(test_data)} 个上下文项\n")
    
    # 测试不同阶段的上下文生成
    print("2. 测试不同阶段的上下文生成...")
    test_stages = [
        ("requirement_analysis", "product_manager"),
        ("technical_design", "tech_lead"),
        ("frontend_development", "frontend_dev"),
        ("backend_development", "backend_dev"),
        ("testing", "qa_engineer")
    ]
    
    total_old_size = 0
    total_new_size = 0
    
    for stage, role in test_stages:
        # 生成优化后的上下文
        optimized_context = context_manager.get_context_for_stage(stage, role)
        optimized_size = len(optimized_context)
        
        # 模拟旧的简单拼接方式
        old_context = str(test_data)
        old_size = len(old_context)
        
        total_old_size += old_size
        total_new_size += optimized_size
        
        print(f"   {stage} ({role}):")
        print(f"     旧方式大小: {old_size:,} 字符")
        print(f"     新方式大小: {optimized_size:,} 字符")
        print(f"     节省: {old_size - optimized_size:,} 字符 ({((old_size - optimized_size) / old_size * 100):.1f}%)")
        print(f"     优化后内容预览: {optimized_context[:200]}...")
        print()
    
    # 统计总体效果
    print("3. 总体效果统计...")
    print(f"   总Token节省: {total_old_size - total_new_size:,} 字符")
    print(f"   平均节省比例: {((total_old_size - total_new_size) / total_old_size * 100):.1f}%")
    
    # 获取上下文统计信息
    stats = context_manager.get_context_stats()
    print(f"\n4. 上下文统计信息:")
    print(f"   总上下文项: {stats['total_items']}")
    print(f"   总大小: {stats['total_size']:,} 字符")
    print(f"   按优先级分布:")
    for priority, data in stats['by_priority'].items():
        print(f"     {priority}: {data['count']} 项, {data['size']:,} 字符")
    print(f"   按类型分布:")
    for context_type, data in stats['by_type'].items():
        print(f"     {context_type}: {data['count']} 项, {data['size']:,} 字符")
    
    # 测试缓存效果
    print(f"\n5. 测试缓存效果...")
    start_time = time.time()
    for _ in range(10):
        context_manager.get_context_for_stage("frontend_development", "frontend_dev")
    cache_time = time.time() - start_time
    print(f"   10次缓存查询耗时: {cache_time:.3f} 秒")
    
    # 清理测试文件
    import shutil
    shutil.rmtree(test_project_dir)
    print(f"\n6. 清理测试文件完成")
    
    print(f"\n=== 测试完成 ===")
    print(f"智能上下文管理器显著减少了Token使用，平均节省 {((total_old_size - total_new_size) / total_old_size * 100):.1f}% 的Token消耗！")

if __name__ == "__main__":
    test_context_manager() 