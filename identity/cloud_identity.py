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
import jieba
import jieba.posseg as pseg

# 配置
API_KEY = "sk-1d1858ada7d442bc82010556fb20718c"
BASE_URL = "https://api.deepseek.com/v1"

# 系统提示词文件路径
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "system_prompts.txt")

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

# 配置jieba分词
jieba.initialize()
# 添加车载领域专业词汇
jieba.add_word('车载系统', freq=1000, tag='n')
jieba.add_word('车机系统', freq=1000, tag='n')
jieba.add_word('车载蓝牙', freq=1000, tag='n')
jieba.add_word('车载WiFi', freq=1000, tag='n')
jieba.add_word('车载以太网', freq=1000, tag='n')
jieba.add_word('车载导航', freq=1000, tag='n')
jieba.add_word('车载娱乐', freq=1000, tag='n')
jieba.add_word('车载诊断', freq=1000, tag='n')
jieba.add_word('车载设置', freq=1000, tag='n')
jieba.add_word('车载UI', freq=1000, tag='n')
jieba.add_word('车载UX', freq=1000, tag='n')
jieba.add_word('车载应用', freq=1000, tag='n')
jieba.add_word('车载驱动', freq=1000, tag='n')
jieba.add_word('车载安全', freq=1000, tag='n')
jieba.add_word('车载通信', freq=1000, tag='n')
jieba.add_word('车载设备', freq=1000, tag='n')
jieba.add_word('车载性能', freq=1000, tag='n')
jieba.add_word('车载模块', freq=1000, tag='n')
jieba.add_word('车载框架', freq=1000, tag='n')
jieba.add_word('车载架构', freq=1000, tag='n')
jieba.add_word('车载服务', freq=1000, tag='n')
jieba.add_word('车载功能', freq=1000, tag='n')
jieba.add_word('车载接口', freq=1000, tag='n')
jieba.add_word('车载协议', freq=1000, tag='n')
jieba.add_word('车载标准', freq=1000, tag='n')
jieba.add_word('车载规范', freq=1000, tag='n')
jieba.add_word('车载开发', freq=1000, tag='n')
jieba.add_word('车载测试', freq=1000, tag='n')
jieba.add_word('车载调试', freq=1000, tag='n')
jieba.add_word('车载优化', freq=1000, tag='n')
jieba.add_word('车载定制', freq=1000, tag='n')
jieba.add_word('车载适配', freq=1000, tag='n')
jieba.add_word('车载集成', freq=1000, tag='n')
jieba.add_word('车载部署', freq=1000, tag='n')
jieba.add_word('车载维护', freq=1000, tag='n')
jieba.add_word('车载升级', freq=1000, tag='n')
jieba.add_word('车载修复', freq=1000, tag='n')
jieba.add_word('车载更新', freq=1000, tag='n')
jieba.add_word('车载版本', freq=1000, tag='n')
jieba.add_word('车载发布', freq=1000, tag='n')
jieba.add_word('车载迭代', freq=1000, tag='n')
jieba.add_word('车载演进', freq=1000, tag='n')
jieba.add_word('车载演进', freq=1000, tag='n')
jieba.add_word('车载演进', freq=1000, tag='n')

# 定义关键词词性
KEYWORD_TAGS = {'n', 'v', 'a', 'eng', 'x'}  # 名词、动词、形容词、英文、其他

# 定义需要过滤的代码相关模式
CODE_PATTERNS = [
    r'[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)',  # 函数调用
    r'[A-Za-z_][A-Za-z0-9_]*\s*=\s*[^;]+',   # 变量赋值
    r'[A-Za-z_][A-Za-z0-9_]*\s*:',           # 标签或字典键
    r'[A-Za-z_][A-Za-z0-9_]*\s*\{[^}]*\}',   # 代码块
    r'[A-Za-z_][A-Za-z0-9_]*\s*\[[^\]]*\]',  # 数组或列表
    r'[A-Za-z_][A-Za-z0-9_]*\s*<[^>]*>',     # 模板或泛型
    r'[A-Za-z_][A-Za-z0-9_]*\s*\.\s*[A-Za-z0-9_]+',  # 对象属性或方法
    r'[A-Za-z_][A-Za-z0-9_]*\s*\+\s*[A-Za-z0-9_]+',  # 字符串拼接
    r'[A-Za-z_][A-Za-z0-9_]*\s*-\s*[A-Za-z0-9_]+',   # 减法运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*\*\s*[A-Za-z0-9_]+',  # 乘法运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\s*[A-Za-z0-9_]+',   # 除法运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*%\s*[A-Za-z0-9_]+',   # 取模运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*&\s*[A-Za-z0-9_]+',   # 位与运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*\|\s*[A-Za-z0-9_]+',  # 位或运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*\^\s*[A-Za-z0-9_]+',  # 位异或运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*<<\s*[A-Za-z0-9_]+',  # 左移运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*>>\s*[A-Za-z0-9_]+',  # 右移运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*==\s*[A-Za-z0-9_]+',  # 等于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*!=\s*[A-Za-z0-9_]+',  # 不等于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*>=\s*[A-Za-z0-9_]+',  # 大于等于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*<=\s*[A-Za-z0-9_]+',  # 小于等于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*>\s*[A-Za-z0-9_]+',   # 大于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*<\s*[A-Za-z0-9_]+',   # 小于运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*&&\s*[A-Za-z0-9_]+',  # 逻辑与运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*\|\|\s*[A-Za-z0-9_]+', # 逻辑或运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*!\s*[A-Za-z0-9_]+',   # 逻辑非运算
    r'[A-Za-z_][A-Za-z0-9_]*\s*\?\s*[A-Za-z0-9_]+',  # 三元运算符
    r'[A-Za-z_][A-Za-z0-9_]*\s*:\s*[A-Za-z0-9_]+',   # 条件运算符
    r'[A-Za-z_][A-Za-z0-9_]*\s*,\s*[A-Za-z0-9_]+',   # 逗号分隔
    r'[A-Za-z_][A-Za-z0-9_]*\s*;\s*[A-Za-z0-9_]+',   # 分号分隔
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # 单行注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # 多行注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Python注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # SQL注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # HTML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # CSS注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # JavaScript注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Shell注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # Lua注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*%%.*',                # MATLAB注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # Haskell注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # C++注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Ruby注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # SQL注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # XML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # C注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # Java注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Perl注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # VBScript注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # SGML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # PHP注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # C#注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Python注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # SQL注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # HTML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # CSS注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # JavaScript注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Shell注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # Lua注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*%%.*',                # MATLAB注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # Haskell注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # C++注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Ruby注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # SQL注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # XML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # C注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # Java注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*#.*',                 # Perl注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*--.*',                # VBScript注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*<!--.*-->',           # SGML注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*/\*.*\*/',            # PHP注释
    r'[A-Za-z_][A-Za-z0-9_]*\s*//.*',                # C#注释
]

def is_code_like(text: str) -> bool:
    """检查文本是否像代码"""
    for pattern in CODE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def extract_keywords(text: str) -> List[str]:
    """使用jieba分词和语义分析提取关键词"""
    # 使用jieba进行分词和词性标注
    words = pseg.cut(text)
    
    # 提取关键词
    keywords = []
    current_phrase = []
    
    # 定义需要过滤的词性
    FILTER_TAGS = {'x', 'm', 'q', 'r', 'p', 'c', 'u', 'e', 'y', 'o', 'w', 'i'}  # 过滤掉标点、数词、代词等
    
    # 定义需要过滤的常见无意义词
    MEANINGLESS_WORDS = {
        '这个', '那个', '这些', '那些', '什么', '怎么', '如何', '为什么', '因为', '所以', 
        '但是', '然而', '然后', '接着', '最后', '首先', '其次', '再次', '总之', '总结', 
        '例如', '比如', '如果', '那么', '可以', '应该', '需要', '必须', '可能', '也许', 
        '大概', '大约', '左右', '上下', '前后', '内外', '大小', '多少', '好坏', '快慢', 
        '高低', '深浅', '远近', '轻重', '长短', '宽窄', '厚薄', '粗细', '软硬', '冷热', 
        '干湿', '明暗', '动静', '早晚', '先后', '新旧', '老幼', '男女', '老少',
        # 代码相关词
        'class', 'def', 'return', 'if', 'else', 'for', 'while', 'try', 'except', 
        'import', 'from', 'as', 'in', 'is', 'not', 'and', 'or', 'True', 'False', 
        'None', 'self', 'this', 'public', 'private', 'protected', 'static', 'void',
        'int', 'float', 'double', 'string', 'bool', 'char', 'byte', 'short', 'long',
        'const', 'final', 'abstract', 'interface', 'extends', 'implements', 'super',
        'new', 'null', 'break', 'continue', 'switch', 'case', 'default', 'throw',
        'throws', 'catch', 'finally', 'package', 'import', 'export', 'require',
        'module', 'function', 'var', 'let', 'const', 'async', 'await', 'yield',
        'generator', 'iterator', 'promise', 'callback', 'closure', 'scope', 'context',
        'prototype', 'constructor', 'instance', 'object', 'array', 'map', 'set',
        'weakmap', 'weakset', 'symbol', 'proxy', 'reflect', 'promise', 'async',
        'await', 'generator', 'iterator', 'yield', 'module', 'export', 'import',
        'require', 'define', 'amd', 'commonjs', 'es6', 'es2015', 'es2016', 'es2017',
        'es2018', 'es2019', 'es2020', 'es2021', 'es2022', 'typescript', 'flow',
        'babel', 'webpack', 'rollup', 'parcel', 'vite', 'jest', 'mocha', 'chai',
        'sinon', 'enzyme', 'cypress', 'puppeteer', 'selenium', 'nightwatch', 'karma',
        'jasmine', 'ava', 'tape', 'tap', 'node', 'npm', 'yarn', 'pnpm', 'bun',
        'deno', 'react', 'vue', 'angular', 'svelte', 'solid', 'preact', 'inferno',
        'lit', 'stencil', 'alpine', 'stimulus', 'htmx', 'tailwind', 'bootstrap',
        'material', 'antd', 'element', 'vuetify', 'quasar', 'ionic', 'capacitor',
        'cordova', 'electron', 'tauri', 'nwjs', 'neutralino', 'sciter', 'flutter',
        'reactnative', 'weex', 'uni-app', 'taro', 'remax', 'rax', 'chameleon',
        'mpvue', 'megalo', 'nanachi', 'kbone', 'omi', 'pre', 'svelte', 'solid',
        'alpine', 'stimulus', 'htmx', 'tailwind', 'bootstrap', 'material', 'antd',
        'element', 'vuetify', 'quasar', 'ionic', 'capacitor', 'cordova', 'electron',
        'tauri', 'nwjs', 'neutralino', 'sciter', 'flutter', 'reactnative', 'weex',
        'uni-app', 'taro', 'remax', 'rax', 'chameleon', 'mpvue', 'megalo', 'nanachi',
        'kbone', 'omi', 'pre', 'svelte', 'solid', 'alpine', 'stimulus', 'htmx',
        'tailwind', 'bootstrap', 'material', 'antd', 'element', 'vuetify', 'quasar',
        'ionic', 'capacitor', 'cordova', 'electron', 'tauri', 'nwjs', 'neutralino',
        'sciter', 'flutter', 'reactnative', 'weex', 'uni-app', 'taro', 'remax',
        'rax', 'chameleon', 'mpvue', 'megalo', 'nanachi', 'kbone', 'omi', 'pre'
    }
    
    for word, flag in words:
        # 如果是关键词词性，添加到当前短语
        if flag in KEYWORD_TAGS and flag not in FILTER_TAGS:
            current_phrase.append(word)
        # 如果不是关键词词性，且当前短语不为空，则处理当前短语
        elif current_phrase:
            # 合并当前短语
            phrase = ''.join(current_phrase)
            # 过滤掉太短的词、代码片段和无意义词
            if (len(phrase) > 2 and 
                not is_code_like(phrase) and 
                phrase not in MEANINGLESS_WORDS and
                not any(word in MEANINGLESS_WORDS for word in phrase)):
                # 检查是否包含中文
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in phrase)
                # 检查是否是纯英文的类名或方法名
                is_english_only = all(ord(char) < 128 for char in phrase)
                is_class_or_method = (phrase[0].isupper() or phrase.startswith('get') or 
                                    phrase.startswith('set') or phrase.startswith('is'))
                
                # 如果包含中文，或者不是纯英文的类名/方法名，则添加到关键词列表
                if has_chinese or (not is_english_only and not is_class_or_method):
                    keywords.append(phrase)
            current_phrase = []
    
    # 处理最后一个短语
    if current_phrase:
        phrase = ''.join(current_phrase)
        if (len(phrase) > 2 and 
            not is_code_like(phrase) and 
            phrase not in MEANINGLESS_WORDS and
            not any(word in MEANINGLESS_WORDS for word in phrase)):
            # 检查是否包含中文
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in phrase)
            # 检查是否是纯英文的类名或方法名
            is_english_only = all(ord(char) < 128 for char in phrase)
            is_class_or_method = (phrase[0].isupper() or phrase.startswith('get') or 
                                phrase.startswith('set') or phrase.startswith('is'))
            
            # 如果包含中文，或者不是纯英文的类名/方法名，则添加到关键词列表
            if has_chinese or (not is_english_only and not is_class_or_method):
                keywords.append(phrase)
    
    # 去重
    keywords = list(set(keywords))
    
    # 过滤掉纯数字和纯符号
    keywords = [word for word in keywords if not word.isdigit() and not all(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in word)]
    
    return keywords

def process_user_input(text: str) -> str:
    """处理用户输入，提取关键词并更新系统提示词"""
    keywords_list = extract_keywords(text)
    if keywords_list:
        dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
        added_prompts = []
        
        for keyword in keywords_list:
            if not dynamic_prompts._has_similar_prompt(keyword, dynamic_prompts.user_prompts):
                if dynamic_prompts.add(keyword, is_user_input=True):
                    added_prompts.append(keyword)
                    console.print(f"[green]已添加用户输入关键词: {keyword}[/green]")
                else:
                    console.print(f"[yellow]关键词 '{keyword}' 与现有内容相似，已跳过[/yellow]")
        
        if added_prompts:
            return " ".join(added_prompts)
    return None

def process_assistant_output(text: str) -> str:
    """处理助手输出，提取关键词并更新系统提示词"""
    keywords_list = extract_keywords(text)
    if keywords_list:
        dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
        added_prompts = []
        
        for keyword in keywords_list:
            if not dynamic_prompts._has_similar_prompt(keyword, dynamic_prompts.model_prompts):
                if dynamic_prompts.add(keyword, is_user_input=False):
                    added_prompts.append(keyword)
                    console.print(f"[green]已添加模型生成关键词: {keyword}[/green]")
                else:
                    console.print(f"[yellow]关键词 '{keyword}' 与现有内容相似，已跳过[/yellow]")
        
        if added_prompts:
            return " ".join(added_prompts)
    return None

def load_system_prompts() -> str:
    """加载系统提示词"""
    try:
        dynamic_prompts = DynamicPrompts(PROMPTS_FILE)
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        base_match = re.search(r'BASE_PROMPT = """(.*?)"""', content, re.DOTALL)
        if base_match:
            base_prompt = base_match.group(1)
            # 组合用户输入和模型生成的关键词
            all_prompts = []
            if dynamic_prompts.user_prompts:
                all_prompts.append("用户输入的关键词：")
                all_prompts.extend([f"- {p}" for p in dynamic_prompts.user_prompts])
            if dynamic_prompts.model_prompts:
                all_prompts.append("模型生成的关键词：")
                all_prompts.extend([f"- {p}" for p in dynamic_prompts.model_prompts])
            if all_prompts:
                base_prompt += "\n\n补充知识：\n" + "\n".join(all_prompts)
            return base_prompt
    except Exception as e:
        console.print(f"[yellow]警告: 无法加载系统提示词文件: {str(e)}[/yellow]")
    return SYSTEM_PROMPT

class ContentValidator:
    """内容验证器，使用AI判断生成内容是否符合用户需求"""
    def __init__(self, client):
        self.client = client
        self.validation_prompt = """请判断以下回答是否完全符合用户的需求。请从以下几个方面进行评估：
1. 内容相关性：回答是否直接解决了用户的问题
2. 技术准确性：技术描述是否准确无误
3. 完整性：是否涵盖了所有必要的技术要点
4. 专业性：是否使用了正确的专业术语
5. 实用性：是否提供了可操作的技术方案

请按照以下格式输出评估结果：
[验证状态]：通过/不通过
[评估维度]：
1. 内容相关性：[评分] - [详细说明]
2. 技术准确性：[评分] - [详细说明]
3. 完整性：[评分] - [详细说明]
4. 专业性：[评分] - [详细说明]
5. 实用性：[评分] - [详细说明]
[总体评价]：[总结性评价]
[改进建议]：[具体的改进建议]"""

    async def validate_content(self, user_input: str, generated_content: str) -> tuple[bool, str]:
        """验证生成内容是否符合用户需求"""
        try:
            console.print("\n[cyan]正在进行内容验证...[/cyan]")
            
            messages = [
                {"role": "system", "content": self.validation_prompt},
                {"role": "user", "content": f"用户问题：{user_input}\n\n生成回答：{generated_content}"}
            ]
            
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            validation_result = response.choices[0].message.content
            
            # 解析验证结果
            is_valid = "通过" in validation_result.split("\n")[0]
            
            # 显示验证结果
            console.print("\n[bold]验证结果：[/bold]")
            console.print(Panel(
                validation_result,
                title="[cyan]AI验证报告[/cyan]",
                border_style="blue"
            ))
            
            if is_valid:
                console.print("[green]✓ 内容验证通过[/green]")
            else:
                console.print("[yellow]⚠ 内容验证未通过，将尝试重新生成[/yellow]")
            
            return is_valid, validation_result
            
        except Exception as e:
            console.print(f"[red]验证过程出错: {str(e)}[/red]")
            return False, f"验证过程出错: {str(e)}"

class AndroidCarBot:
    def __init__(self):
        try:
            self.client = OpenAI(
                api_key=API_KEY,
                base_url=BASE_URL
            )
            self.conversation_history = []
            self.system_prompt = load_system_prompts()
            self.validator = ContentValidator(self.client)
        except Exception as e:
            console.print(f"[bold red]初始化失败: {str(e)}[/bold red]")
            raise
        
    async def validate_response(self, user_input: str, text: str) -> tuple[bool, str]:
        """使用AI验证响应是否符合要求"""
        return await self.validator.validate_content(user_input, text)
        
    async def generate(self, prompt: str, max_retries: int = 3) -> str:
        """生成响应"""
        # 处理用户输入
        new_prompt = process_user_input(prompt)
        if new_prompt:
            self.system_prompt = load_system_prompts()
            console.print("[green]系统提示词已更新[/green]")
            
        for attempt in range(max_retries):
            try:
                console.print(f"\n[cyan]第{attempt + 1}次生成尝试[/cyan]")
                
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
                    title=f"[cyan]生成内容[/cyan]",
                    border_style="yellow"
                ))
                
                # 验证响应
                is_valid, validation_msg = await self.validate_response(prompt, content)
                
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
                    if attempt < max_retries - 1:
                        console.print(f"[yellow]正在尝试第{attempt + 2}次生成...[/yellow]")
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
    _last_added_prompt = None  # 记录最后添加的提示词
    
    def __new__(cls, file_path=None):
        if cls._instance is None:
            cls._instance = super(DynamicPrompts, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, file_path=None):
        if not self._initialized:
            self.file_path = file_path
            self.user_prompts = []  # 用户输入的关键词
            self.model_prompts = []  # 模型生成的关键词
            self.load()
            DynamicPrompts._initialized = True
    
    def load(self):
        """加载动态提示词"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 提取用户输入的关键词
            user_match = re.search(r'USER_PROMPTS = \[(.*?)\]', content, re.DOTALL)
            if user_match:
                array_content = user_match.group(1).strip()
                if array_content:
                    prompts = [p.strip().strip('"').strip("'") for p in array_content.split(',') if p.strip()]
                    self.user_prompts = [p for p in prompts if p]
            
            # 提取模型生成的关键词
            model_match = re.search(r'MODEL_PROMPTS = \[(.*?)\]', content, re.DOTALL)
            if model_match:
                array_content = model_match.group(1).strip()
                if array_content:
                    prompts = [p.strip().strip('"').strip("'") for p in array_content.split(',') if p.strip()]
                    self.model_prompts = [p for p in prompts if p]
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
                new_content = f'BASE_PROMPT = """{base_prompt}"""\n\n# 用户输入的关键词\nUSER_PROMPTS = []\n\n# 模型生成的关键词\nMODEL_PROMPTS = []'
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.user_prompts = []
                self.model_prompts = []
        except Exception as e:
            console.print(f"[red]修复文件失败: {str(e)}[/red]")
    
    def save(self):
        """保存动态提示词"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 格式化用户输入的关键词
            formatted_user_prompts = [f'  "{p}"' for p in self.user_prompts]
            # 格式化模型生成的关键词
            formatted_model_prompts = [f'  "{p}"' for p in self.model_prompts]
            
            # 更新用户输入的关键词
            new_content = re.sub(
                r'USER_PROMPTS = \[.*?\]',
                f'USER_PROMPTS = [\n{",\n".join(formatted_user_prompts)}\n]',
                content,
                flags=re.DOTALL
            )
            
            # 更新模型生成的关键词
            new_content = re.sub(
                r'MODEL_PROMPTS = \[.*?\]',
                f'MODEL_PROMPTS = [\n{",\n".join(formatted_model_prompts)}\n]',
                new_content,
                flags=re.DOTALL
            )
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            console.print(f"[red]保存动态提示词失败: {str(e)}[/red]")
    
    def add(self, prompt: str, is_user_input: bool = True) -> bool:
        """添加新的提示词"""
        # 移除换行符和多余空格
        prompt = prompt.replace('\n', ' ').strip()
        
        # 检查是否与最后添加的提示词相似
        if self._last_added_prompt and self._is_similar(prompt, self._last_added_prompt):
            console.print(f"[yellow]警告: 新提示词与刚添加的提示词 '{self._last_added_prompt}' 相似度较高[/yellow]")
            return False
            
        # 检查是否与现有提示词有相似内容
        target_prompts = self.user_prompts if is_user_input else self.model_prompts
        if not self._has_similar_prompt(prompt, target_prompts):
            if is_user_input:
                self.user_prompts.append(prompt)
            else:
                self.model_prompts.append(prompt)
            self._last_added_prompt = prompt  # 更新最后添加的提示词
            self.save()
            return True
        return False
    
    def _is_similar(self, prompt1: str, prompt2: str) -> bool:
        """检查两个提示词是否相似"""
        # 如果其中一个完全包含另一个，认为是相似的
        if prompt1 in prompt2 or prompt2 in prompt1:
            return True
        
        # 提取关键词
        keywords1 = set(re.findall(r'\w+', prompt1.lower()))
        keywords2 = set(re.findall(r'\w+', prompt2.lower()))
        
        if not keywords1 or not keywords2:
            return False
        
        # 计算重叠率
        overlap = len(keywords1 & keywords2)
        total = len(keywords1 | keywords2)
        
        # 如果关键词完全重叠，认为是相似的
        if overlap == len(keywords1) or overlap == len(keywords2):
            return True
        
        # 如果重叠率超过70%，认为是相似的
        return total > 0 and overlap / total > 0.7
    
    def _has_similar_prompt(self, new_prompt: str, target_prompts: List[str] = None) -> bool:
        """检查是否有相似的提示词"""
        if target_prompts is None:
            target_prompts = self.user_prompts + self.model_prompts
        for prompt in target_prompts:
            if self._is_similar(new_prompt, prompt):
                console.print(f"[yellow]警告: 新提示词与现有提示词 '{prompt}' 相似度较高[/yellow]")
                return True
        return False
    
    def reset(self):
        """重置动态提示词（仅在程序退出时调用）"""
        self.user_prompts = []
        self.model_prompts = []
        self._last_added_prompt = None
        self.save()

def check_environment():
    """检查运行环境"""
    try:
        # 检查网络连接
        import requests
        requests.get(BASE_URL, timeout=10)
        return True
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]错误: 无法连接到DeepSeek API: {str(e)}[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]错误: 发生未知错误: {str(e)}[/bold red]")
        return False

async def main():
    try:
        # 检查环境
        if not check_environment():
            console.print("[bold red]程序无法正常运行，请检查网络连接后重试[/bold red]")
            input("按回车键退出...")
            return

        console.print(Panel.fit(
            "[bold green]欢迎使用Android13车机系统开发助手[/bold green]\n"
            "输入'q'退出程序，动态提示词将会清空，请及时保存所需提示词\n"
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
                    
                response = await bot.generate(user_input)
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
    import asyncio
    asyncio.run(main())