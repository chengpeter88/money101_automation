from setuptools import setup, find_packages
import os

# 檢查 README.md 是否存在
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name="money101_automation",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A web scraping project for credit card and personal loan information.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chengpeter88/money101_automation",
    packages=find_packages(),  # 不指定 where，會找到當前目錄下所有包
    # 移除 package_dir 設定，或確保目錄結構正確
    install_requires=[
        "selenium",
        "webdriver-manager",
        "pandas",
        "openpyxl",
        "beautifulsoup4",
        "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)