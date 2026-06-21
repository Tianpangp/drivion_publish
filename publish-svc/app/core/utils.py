"""
通用工具函数
"""
import uuid
import tarfile
import zipfile
import io
import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path


def generate_id(prefix: str = "") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        str: 唯一ID
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id


def get_current_timestamp() -> datetime:
    """
    获取当前时间戳
    
    Returns:
        datetime: 当前时间
    """
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        fmt: 格式化字符串
        
    Returns:
        Optional[str]: 格式化后的字符串
    """
    if dt is None:
        return None
    return dt.strftime(fmt)


def snake_to_camel(snake_str: str) -> str:
    """
    蛇形命名转驼峰命名
    
    Args:
        snake_str: 蛇形命名字符串
        
    Returns:
        str: 驼峰命名字符串
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    驼峰命名转蛇形命名
    
    Args:
        camel_str: 驼峰命名字符串
        
    Returns:
        str: 蛇形命名字符串
    """
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()


def dict_snake_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    字典键从蛇形转驼峰
    
    Args:
        data: 蛇形命名的字典
        
    Returns:
        Dict: 驼峰命名的字典
    """
    return {snake_to_camel(k): v for k, v in data.items()}


def parse_tar_package(file_data: bytes) -> Dict[str, Any]:
    """
    解析 tar.gz 包，提取依赖信息
    
    Args:
        file_data: tar.gz 文件数据
        
    Returns:
        Dict: 包含依赖信息的字典
    """
    result = {
        "dependencies": [],
        "python_version": None,
        "readme": None,
        "setup_info": {}
    }
    
    try:
        # 使用 BytesIO 创建文件对象
        file_obj = io.BytesIO(file_data)
        
        # 打开 tar 文件
        with tarfile.open(fileobj=file_obj, mode='r:*') as tar:
            # 查找 requirements.txt
            for member in tar.getmembers():
                if member.name.endswith('requirements.txt'):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode('utf-8', errors='ignore')
                        result["dependencies"] = [
                            line.strip() for line in content.split('\n')
                            if line.strip() and not line.strip().startswith('#')
                        ]
                        f.close()
                
                # 查找 README
                elif 'README' in member.name.upper():
                    f = tar.extractfile(member)
                    if f:
                        result["readme"] = f.read().decode('utf-8', errors='ignore')
                        f.close()
                
                # 查找 setup.py 获取版本信息
                elif member.name.endswith('setup.py'):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode('utf-8', errors='ignore')
                        # 简单解析 python_requires
                        python_match = re.search(r'python_requires=[\'"]([^\'"]+)[\'"]', content)
                        if python_match:
                            result["python_version"] = python_match.group(1)
                        f.close()
    
    except Exception as e:
        print(f"解析 tar 包失败: {e}")
    
    return result


def parse_zip_package(file_data: bytes) -> Dict[str, Any]:
    """
    解析 zip 包，提取依赖信息
    
    Args:
        file_data: zip 文件数据
        
    Returns:
        Dict: 包含依赖信息的字典
    """
    result = {
        "dependencies": [],
        "readme": None
    }
    
    try:
        file_obj = io.BytesIO(file_data)
        
        with zipfile.ZipFile(file_obj, 'r') as zip_file:
            # 查找 requirements.txt 或 README
            for filename in zip_file.namelist():
                if filename.endswith('requirements.txt'):
                    content = zip_file.read(filename).decode('utf-8', errors='ignore')
                    result["dependencies"] = [
                        line.strip() for line in content.split('\n')
                        if line.strip() and not line.strip().startswith('#')
                    ]
                
                elif 'README' in filename.upper():
                    result["readme"] = zip_file.read(filename).decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"解析 zip 包失败: {e}")
    
    return result


def compute_file_hash(file_data: bytes) -> Tuple[str, str]:
    """
    计算文件的 MD5 和 SHA256 哈希值
    
    Args:
        file_data: 文件二进制数据
        
    Returns:
        Tuple[str, str]: (MD5, SHA256) 哈希值
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    md5_hash.update(file_data)
    sha256_hash.update(file_data)
    
    return md5_hash.hexdigest(), sha256_hash.hexdigest()
