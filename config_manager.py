import os
import sys
import json

def get_bundled_resource_path(relative_path):
    """
    读取静态资源路径。
    自动兼容 PyInstaller 打包后的 _MEIPASS 临时目录和本地开发环境。
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def get_user_data_path(relative_path):
    """
    读取用户数据/配置路径。
    确保打包成 exe 后，配置文件依然保存在 exe 同级目录下，而不是临时目录。
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def load_config(config_path):
    """加载本地 JSON 配置文件，若不存在则返回默认配置"""
    default_cfg = {
        "last_dir": os.getcwd(),
        "basemap": "GeoQ极简灰 (国内/极速/推荐)",
        "use_proxy": False,  # <--- 新增: 默认不开启代理
        "proxy_port": "7890",  # <--- 新增: 默认 Clash 端口
        "sens": 8.0, "bw": 0.06, "thresh": 0.05, "alpha": 0.85,
        "show_points": True, "point_size": 10, "show_colorbar": True, "show_subway": True,
        "show_names": True, "show_mask": True, "mask_alpha": 0.55, "theme": "经典绿黄红", "dpi_str": "400 (高清报告)"
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                default_cfg.update(json.load(f))
        except Exception as e:
            print(f"读取配置失败: {e}")
    return default_cfg

def save_config(config_path, current_cfg):
    """将当前 UI 状态持久化保存到本地 JSON"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(current_cfg, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置失败: {e}")