"""
知识库管理器
用于管理和检索各种技术文档和学习资源
"""

import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeResource:
    """知识资源数据结构"""
    title: str
    url: str
    description: str
    category: str


class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self, config_path: str = "config/knowledge_base.yaml"):
        self.config_path = config_path
        self.resources = self._load_resources()
    
    def _load_resources(self) -> Dict[str, List[KnowledgeResource]]:
        """加载知识库配置"""
        if not os.path.exists(self.config_path):
            return {}
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        resources = {}
        for category, items in config.items():
            resources[category] = []
            for item in items:
                resource = KnowledgeResource(
                    title=item['title'],
                    url=item['url'],
                    description=item['description'],
                    category=category
                )
                resources[category].append(resource)
        
        return resources
    
    def get_resources_by_category(self, category: str) -> List[KnowledgeResource]:
        """根据分类获取资源"""
        return self.resources.get(category, [])
    
    def search_resources(self, keyword: str) -> List[KnowledgeResource]:
        """搜索资源"""
        results = []
        keyword_lower = keyword.lower()
        
        for category, resources in self.resources.items():
            for resource in resources:
                if (keyword_lower in resource.title.lower() or 
                    keyword_lower in resource.description.lower() or
                    keyword_lower in resource.category.lower()):
                    results.append(resource)
        
        return results
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.resources.keys())
    
    def get_resource_by_title(self, title: str) -> Optional[KnowledgeResource]:
        """根据标题获取资源"""
        for category, resources in self.resources.items():
            for resource in resources:
                if resource.title == title:
                    return resource
        return None
    
    def format_resources_for_agent(self, resources: List[KnowledgeResource]) -> str:
        """格式化资源为Agent可用的格式"""
        if not resources:
            return "未找到相关资源"
        
        formatted = []
        for resource in resources:
            formatted.append(f"📚 **{resource.title}**")
            formatted.append(f"   描述: {resource.description}")
            formatted.append(f"   链接: {resource.url}")
            formatted.append(f"   分类: {resource.category}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def get_developer_resources(self) -> List[KnowledgeResource]:
        """获取开发工程师相关资源"""
        dev_resources = []
        dev_categories = ['developer_docs', 'backend_resources', 'frontend_resources']
        
        for category in dev_categories:
            dev_resources.extend(self.get_resources_by_category(category))
        
        return dev_resources
    
    def get_ai_ml_resources(self) -> List[KnowledgeResource]:
        """获取AI/ML工程师相关资源"""
        ai_resources = []
        ai_categories = ['ai_ml_docs', 'data_science']
        
        for category in ai_categories:
            ai_resources.extend(self.get_resources_by_category(category))
        
        return ai_resources
    
    def get_pm_resources(self) -> List[KnowledgeResource]:
        """获取产品经理相关资源"""
        return self.get_resources_by_category('pm_resources')
    
    def get_qa_resources(self) -> List[KnowledgeResource]:
        """获取测试工程师相关资源"""
        return self.get_resources_by_category('qa_resources')
    
    def get_devops_resources(self) -> List[KnowledgeResource]:
        """获取DevOps工程师相关资源"""
        return self.get_resources_by_category('devops_resources')
    
    def get_security_resources(self) -> List[KnowledgeResource]:
        """获取安全相关资源"""
        return self.get_resources_by_category('security_resources')
    
    def get_best_practices(self) -> List[KnowledgeResource]:
        """获取最佳实践资源"""
        return self.get_resources_by_category('best_practices')
    
    def get_project_management_resources(self) -> List[KnowledgeResource]:
        """获取项目管理资源"""
        return self.get_resources_by_category('project_management')
    
    def get_design_resources(self) -> List[KnowledgeResource]:
        """获取设计资源"""
        return self.get_resources_by_category('design_resources')


# 预定义的资源查询函数
def get_role_specific_resources(role: str) -> List[KnowledgeResource]:
    """根据角色获取特定资源"""
    km = KnowledgeManager()
    
    role_resources = {
        'developer': km.get_developer_resources(),
        'ai_engineer': km.get_ai_ml_resources(),
        'product_manager': km.get_pm_resources(),
        'qa_engineer': km.get_qa_resources(),
        'devops_engineer': km.get_devops_resources(),
        'security_engineer': km.get_security_resources(),
        'designer': km.get_design_resources(),
        'project_manager': km.get_project_management_resources(),
    }
    
    return role_resources.get(role.lower(), [])


def search_knowledge_base(query: str) -> str:
    """搜索知识库并返回格式化结果"""
    km = KnowledgeManager()
    resources = km.search_resources(query)
    return km.format_resources_for_agent(resources)


def get_learning_path(role: str) -> str:
    """获取特定角色的学习路径"""
    km = KnowledgeManager()
    
    learning_paths = {
        'developer': {
            '基础': ['Python官方文档', 'Git官方文档', 'Docker官方文档'],
            '进阶': ['FastAPI官方文档', 'PostgreSQL官方文档', 'Google Python风格指南'],
            '前端': ['React官方文档', 'TypeScript官方文档', 'MDN Web文档']
        },
        'ai_engineer': {
            '基础': ['Python官方文档', 'NumPy官方文档', 'Pandas官方文档'],
            '机器学习': ['Scikit-learn官方文档', 'PyTorch官方文档', 'TensorFlow官方文档'],
            'LLM开发': ['OpenAI API文档', 'LangChain文档', 'Hugging Face文档']
        },
        'product_manager': {
            '基础': ['产品经理入门指南', '需求分析方法论', '敏捷开发宣言'],
            '进阶': ['用户研究方法', '产品设计思维', 'Scrum指南'],
            '设计': ['用户体验设计原则', 'Material Design指南']
        },
        'qa_engineer': {
            '基础': ['Pytest官方文档', 'Selenium官方文档', 'Postman学习中心'],
            '进阶': ['测试驱动开发(TDD)', '性能测试指南', 'Web安全测试指南']
        },
        'devops_engineer': {
            '基础': ['Docker官方文档', 'Git官方文档', 'Jenkins官方文档'],
            '进阶': ['Kubernetes官方文档', 'Prometheus监控文档', 'Terraform官方文档']
        }
    }
    
    if role.lower() not in learning_paths:
        return "未找到该角色的学习路径"
    
    path = learning_paths[role.lower()]
    result = f"📖 **{role} 学习路径**\n\n"
    
    for level, titles in path.items():
        result += f"### {level}\n"
        for title in titles:
            resource = km.get_resource_by_title(title)
            if resource:
                result += f"- [{title}]({resource.url}) - {resource.description}\n"
        result += "\n"
    
    return result


if __name__ == "__main__":
    # 测试知识库管理器
    km = KnowledgeManager()
    
    print("=== 知识库测试 ===")
    print(f"总分类数: {len(km.get_all_categories())}")
    print(f"分类列表: {km.get_all_categories()}")
    
    print("\n=== 搜索测试 ===")
    search_results = km.search_resources("Python")
    print(f"搜索'Python'找到 {len(search_results)} 个结果")
    
    print("\n=== 角色资源测试 ===")
    dev_resources = km.get_developer_resources()
    print(f"开发工程师资源: {len(dev_resources)} 个")
    
    print("\n=== 学习路径测试 ===")
    learning_path = get_learning_path("developer")
    print(learning_path) 