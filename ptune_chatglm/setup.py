from setuptools import setup, find_packages

setup(
    name="ptune_chatglm",      # 建议改成全小写、下划线分隔
    version="0.1",
    packages=find_packages()     # 会自动包含 utils、models 等子包
)