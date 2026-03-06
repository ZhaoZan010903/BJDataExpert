# 🌍 Data Expert | 空间(BJ)大数据分析系统 V2.0
#### 全部使用gemini所写 

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-success.svg)
![GeoPandas](https://img.shields.io/badge/GIS-GeoPandas-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Data Expert 是一款基于 Python 开发的现代化桌面级 GIS 空间分析与数据可视化渲染引擎。
专为城市数据分析、区域热力挖掘和高质量商业报告生成而设计。通过导入包含业务坐标的 Excel 数据源，即可一键生成出版级（最高 600 DPI）的高清空间热力图。

---

## ✨ 核心特性 (Key Features)

### 🚀 高性能流水线渲染引擎
* **一键成图**：自动化执行坐标清洗、墨卡托投影转换、KDE 核密度计算与多图层叠加。
* **出版级画质**：完全解耦的 DPI 控制，支持 200 (极速预览) / 400 (高清报告) / 600 (出版印刷) 无损输出。
* **多模态视觉微调**：内置“经典绿黄红”、“商务冷色蓝”等多种高级配色主题，支持自定义热力灵敏度 (Sens)、收束带宽 (BW) 与噪点过滤。

### 🗺️ 硬核离线底图引擎 (Anti-Scraping Cache)
* **多源无缝切换**：内置高德（标准/路网）、GeoQ（极简灰/藏青蓝）、OSM、CARTO 等国内外顶级专业底图。
* **防封禁下载器**：底层封装智能防死锁机制与浏览器环境伪装，无视最新反爬虫策略。
* **智能缓存雷达**：Zoom 层级物理隔离，支持毫秒级断点急停、静默查漏补缺，以及直观的三色雷达进度指示灯。

### 🎨 高级定制化图层系统
* **动态边界渲染**：支持对行政区划边界进行“高定级”干预（自定义线型、颜色、粗细、透明度）。
* **空间语境增强**：支持域外暗化遮罩（反向 Masking）、地铁网线原色叠加、自适应文本描边防遮挡技术。

### 🎛️ 现代工业级交互界面
* 采用 `CustomTkinter` 构建的现代化选项卡 (Tabview) 布局，彻底告别繁杂的参数堆叠。
* 彻底解耦的**生图精度 (DPI)** 与**底图精度 (Zoom)** 设置。
* 极致流畅的异步多线程调度 (Threading)，彻底告别“假死”，实时反馈控制台日志。

---

## 📂 项目架构 (Directory Structure)

```text
BJDataExpert/
├── main.py                  # 系统主入口 & 异步 UI 调度中心
├── config_manager.py        # 全局配置管理与持久化模块
├── core/                    # 核心计算与渲染引擎
│   ├── data.py              # Excel 数据解析与坐标清洗
│   ├── canvas.py            # 离线底图并发下载与瓦片拼接
│   ├── heatmap.py           # KDE 核密度热力算法
│   ├── subway.py            # 城市地铁线网数据叠加
│   ├── mask.py              # 域外遮罩与高定行政边界渲染
│   └── export.py            # 图例生成、散点打标与高保真输出
├── map_cache/               # 离线瓦片金字塔缓存池 (Git 已配置忽略)
├── requirements.txt         # 项目依赖环境清单
└── README.md                # 项目说明文档
