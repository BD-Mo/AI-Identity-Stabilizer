# cloud_identity.py
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing import List, Dict
import time
import readline
import sys
import os
import json
import re

# 配置
API_KEY = "sk-78437fc819664ddeb0359be48e4f8d7f"
BASE_URL = "https://api.deepseek.com"

# 系统提示词文件路径
PROMPTS_FILE = "system_prompts.txt"

# 系统提示词
SYSTEM_PROMPT = """你現在是【Android13车机系统开发工程师】，必须：
1. 使用Android 13和车载系统开发的专业术语
2. 每句包含车机系统开发相关元素（车载、系统、应用、框架）
3. 使用技术文档和代码注释风格的表达
4. 保持专业和严谨的语气

专业知识范围：
- Android 13系统架构
  * 系统服务层
  * 应用框架层
  * 硬件抽象层
  * Linux内核层
- 车载系统开发
  * 车载UI/UX设计规范
  * 车载应用开发
  * 车载系统定制
  * 车载性能优化
- 车载通信
  * CAN总线通信
  * 车载以太网
  * 车载蓝牙
  * 车载WiFi
- 车载安全
  * 系统安全机制
  * 应用安全
  * 数据安全
  * 通信安全
- 车载驱动
  * 车载设备驱动
  * 传感器驱动
  * 音频驱动
  * 显示驱动
- 车载应用
  * 车载导航
  * 车载娱乐
  * 车载诊断
  * 车载设置

请确保回答专业、准确，并符合车载系统开发规范。"""

# 验证规则
REQUIRED_ELEMENTS = ["车载", "系统", "应用", "框架"]
FORBIDDEN_WORDS = ["魔法", "神秘", "占卜", "炼金术"]

console = Console()

def check_environment():
    """检查运行环境"""
    try:
        # 检查网络连接
        import requests
        requests.get("https://api.deepseek.com", timeout=5)
        return True
    except:
        console.print("[bold red]错误: 无法连接到DeepSeek API，请检查网络连接[/bold red]")
        return False

def save_dynamic_prompt(prompt: str):
    """保存动态提示词"""
    dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
    if dynamic_prompts.add(prompt):
        console.print("[green]系统提示词已更新[/green]")

def load_system_prompts() -> str:
    """加载系统提示词"""
    try:
        dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        base_match = re.search(r'BASE_PROMPT = """(.*?)"""', content, re.DOTALL)
        if base_match:
            base_prompt = base_match.group(1)
            if dynamic_prompts.prompts:
                base_prompt += "\n\n补充知识：\n- " + "\n- ".join(dynamic_prompts.prompts)
            return base_prompt
    except Exception as e:
        console.print(f"[yellow]警告: 无法加载系统提示词文件: {str(e)}[/yellow]")
    return SYSTEM_PROMPT

def extract_keywords(text: str) -> str:
    """从文本中提取关键词并生成提示词"""
    # 提取技术术语
    technical_terms = re.findall(r'[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*', text)
    # 提取中文专业术语
    chinese_terms = re.findall(r'[车载系统应用框架驱动安全通信]+[^，。！？\s]+', text)
    
    # 合并并去重
    all_terms = list(set(technical_terms + chinese_terms))
    # 过滤掉太短的词
    all_terms = [term for term in all_terms if len(term) > 2]
    
    # 生成提示词（不包含换行符）
    if all_terms:
        return " ".join(all_terms[:5])
    return ""

def process_user_input(text: str) -> str:
    """处理用户输入，提取关键词并更新系统提示词"""
    keywords_prompt = extract_keywords(text)
    if keywords_prompt:
        console.print("\n[yellow]检测到用户输入中包含专业术语，是否将其添加到系统提示词中？(y/n)[/yellow]")
        if input().lower() == 'y':
            save_dynamic_prompt(keywords_prompt)
            return keywords_prompt
    return None

def process_assistant_output(text: str) -> str:
    """处理助手输出，提取关键词并更新系统提示词"""
    keywords_prompt = extract_keywords(text)
    if keywords_prompt:
        console.print("\n[yellow]检测到生成内容中包含专业术语，是否将其添加到系统提示词中？(y/n)[/yellow]")
        if input().lower() == 'y':
            save_dynamic_prompt(keywords_prompt)
            return keywords_prompt
    return None

class AndroidCarBot:
    def __init__(self):
        try:
            self.client = OpenAI(
                api_key=API_KEY,
                base_url=BASE_URL
            )
            self.conversation_history = []
            self.system_prompt = load_system_prompts()
        except Exception as e:
            console.print(f"[bold red]初始化失败: {str(e)}[/bold red]")
            raise
        
    def validate_response(self, text: str) -> tuple[bool, str]:
        """验证响应是否符合要求"""
        # 检查必需元素
        required_count = sum(1 for element in REQUIRED_ELEMENTS if element in text)
        if required_count < 2:
            return False, f"必需元素不足，当前包含: {required_count}/2"
            
        # 检查禁止词
        found_forbidden = [word for word in FORBIDDEN_WORDS if word in text]
        if found_forbidden:
            return False, f"包含禁止词: {', '.join(found_forbidden)}"
            
        # 检查专业术语使用
        technical_terms = [
            "Android 13", "车载系统", "系统架构", "应用框架", 
            "硬件抽象", "驱动开发", "性能优化", "安全机制",
            "CAN总线", "车载以太网", "车载蓝牙", "车载WiFi"
        ]
        technical_count = sum(1 for term in technical_terms if term in text)
        if technical_count < 2:
            return False, f"专业术语使用不足，当前包含: {technical_count}/2"
            
        # 检查段落结构
        paragraphs = text.split('\n\n')
        if len(paragraphs) < 2:
            return False, "内容结构不完整，至少需要两个段落"
            
        # 检查技术性表达
        technical_phrases = [
            "系统架构", "开发规范", "技术实现", "性能优化",
            "安全机制", "通信协议", "驱动开发", "应用开发"
        ]
        phrase_count = sum(1 for phrase in technical_phrases if phrase in text)
        if phrase_count < 1:
            return False, "缺少技术性表达"
            
        return True, "验证通过"
        
    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """生成响应"""
        # 处理用户输入
        new_prompt = process_user_input(prompt)
        if new_prompt:
            self.system_prompt = load_system_prompts()
            console.print("[green]系统提示词已更新[/green]")
            
        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history,
                    {"role": "user", "content": prompt}
                ]
                
                response = self.client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000,
                    stream=False
                )
                
                content = response.choices[0].message.content
                
                # 显示生成的内容
                console.print(Panel(
                    Markdown(content),
                    title=f"[cyan]第{attempt + 1}次生成内容[/cyan]",
                    border_style="yellow"
                ))
                
                # 验证响应
                is_valid, validation_msg = self.validate_response(content)
                
                if is_valid:
                    # 保存对话历史
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": content})
                    
                    # 处理助手输出
                    new_prompt = process_assistant_output(content)
                    if new_prompt:
                        self.system_prompt = load_system_prompts()
                        console.print("[green]系统提示词已更新[/green]")
                    
                    return content
                else:
                    console.print(f"[yellow]第{attempt + 1}次生成未通过验证: {validation_msg}[/yellow]")
                    if attempt < max_retries - 1:
                        console.print("[yellow]正在重新生成...[/yellow]")
                        time.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        return f"抱歉，系统无法生成符合要求的回答。\n验证失败原因：{validation_msg}"
                
            except Exception as e:
                console.print(f"[bold red]错误: {str(e)}[/bold red]")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "抱歉，系统暂时无法处理请求，请稍后重试。"

class DynamicPrompts:
    """动态提示词管理类"""
    _instance = None  # 单例实例
    _initialized = False  # 初始化标志
    
    def __new__(cls, file_path=None):
        if cls._instance is None:
            cls._instance = super(DynamicPrompts, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, file_path=None):
        if not self._initialized:
            self.file_path = file_path
            self.prompts = []
            self.load()
            DynamicPrompts._initialized = True
    
    def load(self):
        """加载动态提示词"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            dynamic_match = re.search(r'DYNAMIC_PROMPTS = \[(.*?)\]', content, re.DOTALL)
            if dynamic_match:
                array_content = dynamic_match.group(1).strip()
                if array_content:
                    # 处理多行内容，移除换行符和多余空格
                    prompts = [p.strip().strip('"').strip("'") for p in array_content.split(',') if p.strip()]
                    self.prompts = [p for p in prompts if p]
        except Exception as e:
            console.print(f"[yellow]警告: 加载动态提示词失败: {str(e)}[/yellow]")
            self._repair_file()
    
    def _repair_file(self):
        """修复文件格式"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取基础提示词
            base_match = re.search(r'BASE_PROMPT = """(.*?)"""', content, re.DOTALL)
            if base_match:
                base_prompt = base_match.group(1)
                # 重新写入文件，重置动态提示词
                new_content = f'BASE_PROMPT = """{base_prompt}"""\n\n# 动态添加的系统提示词（JSON格式数组）\nDYNAMIC_PROMPTS = []'
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.prompts = []
        except Exception as e:
            console.print(f"[red]修复文件失败: {str(e)}[/red]")
    
    def save(self):
        """保存动态提示词"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 格式化提示词，确保每个提示词都是一行
            formatted_prompts = [f'  "{p}"' for p in self.prompts]
            
            new_content = re.sub(
                r'DYNAMIC_PROMPTS = \[.*?\]',
                f'DYNAMIC_PROMPTS = [\n{",\n".join(formatted_prompts)}\n]',
                content,
                flags=re.DOTALL
            )
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            console.print(f"[red]保存动态提示词失败: {str(e)}[/red]")
    
    def add(self, prompt: str):
        """添加新的提示词"""
        # 移除换行符和多余空格
        prompt = prompt.replace('\n', ' ').strip()
        
        # 检查是否与现有提示词有相似内容
        if not self._has_similar_prompt(prompt):
            self.prompts.append(prompt)
            self.save()
            return True
        return False
    
    def _has_similar_prompt(self, new_prompt: str) -> bool:
        """检查是否有相似的提示词"""
        # 提取关键词
        new_keywords = set(re.findall(r'\w+', new_prompt.lower()))
        if not new_keywords:
            return False
        
        # 检查与现有提示词的相似度
        for prompt in self.prompts:
            existing_keywords = set(re.findall(r'\w+', prompt.lower()))
            if not existing_keywords:
                continue
            # 如果关键词重叠率超过70%，认为是相似的
            overlap = len(new_keywords & existing_keywords)
            total = len(new_keywords | existing_keywords)
            if total > 0 and overlap / total > 0.7:
                return True
        return False
    
    def reset(self):
        """重置动态提示词（仅在程序退出时调用）"""
        self.prompts = []
        self.save()

def main():
    try:
        # 检查环境
        if not check_environment():
            console.print("[bold red]程序无法正常运行，请检查网络连接后重试[/bold red]")
            input("按回车键退出...")
            return

        console.print(Panel.fit(
            "[bold green]欢迎使用Android13车机系统开发助手[/bold green]\n"
            "输入'q'退出程序\n"
            "输入'clear'清除对话历史",
            title="系统信息"
        ))
        
        bot = AndroidCarBot()
        dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
        
        while True:
            try:
                console.print("[yellow]请输入您的问题：[/yellow]", end="")
                readline.set_startup_hook(lambda: readline.insert_text(""))
                user_input = input()
                
                if user_input.lower() == 'q':
                    # 在退出时重置动态提示词
                    dynamic_prompts.reset()
                    break
                elif user_input.lower() == 'clear':
                    bot.conversation_history = []
                    console.print("[green]对话历史已清除[/green]")
                    continue
                    
                response = bot.generate(user_input)
                console.print(Panel(
                    Markdown(response),
                    title="[cyan]Android13车机系统开发工程师[/cyan]",
                    border_style="blue"
                ))
                
            except KeyboardInterrupt:
                console.print("\n[bold red]程序已终止[/bold red]")
                # 在退出时重置动态提示词
                dynamic_prompts.reset()
                break
                
    except Exception as e:
        console.print(f"[bold red]系统错误: {str(e)}[/bold red]")
    finally:
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()