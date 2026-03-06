import os
import time
import threading
import warnings
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd
import matplotlib

from config_manager import get_user_data_path, load_config, save_config
from core import data, canvas, heatmap, subway, mask, export

matplotlib.use('Agg')
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
ctk.set_appearance_mode("Light")


class HeatmapPipeline:
    @staticmethod
    def execute(params, log_callback):
        start_time = time.time()
        try:
            log_callback("=" * 65)
            log_callback(f"🔵 任务开始 [{time.strftime('%H:%M:%S')}] - 目标文件: {os.path.basename(params['filename'])}")

            # 核心业务流水线
            gdf_wm = data.run(params, log_callback)
            fig, ax, bbox = canvas.run(gdf_wm, params, log_callback)
            cmap = heatmap.run(ax, gdf_wm, params, log_callback)
            subway.run(ax, params, log_callback)
            mask.run(ax, bbox, params, log_callback)
            success = export.run(fig, ax, gdf_wm, cmap, params, log_callback)

            log_callback("-" * 65)
            log_callback(f"🎉 任务完美完成！总计耗时: {time.time() - start_time:.2f} 秒")
            return success

        except Exception as e:
            log_callback(f"❌ 运行崩溃：{str(e)}")
            return False


class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Data Expert | 空间大数据分析系统 V2.0")
        self.geometry("1250x920")
        self.configure(fg_color="#F8F9FA")

        self.config_path = get_user_data_path("config.json")
        self.cfg = load_config(self.config_path)

        self._cancel_download_flag = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ================= UI 左侧控制面板 =================
        self.sidebar = ctk.CTkFrame(self, width=360, corner_radius=0, fg_color="#FFFFFF")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sidebar, text="DATA EXPERT", font=ctk.CTkFont("Arial", 24, "bold"),
                     text_color="#1A73E8").grid(row=0, column=0, pady=(25, 15))

        self.tabview = ctk.CTkTabview(self.sidebar, width=340)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))

        self.tab_base = self.tabview.add("基础设置")
        self.tab_visual = self.tabview.add("视觉与算法")
        self.tab_map = self.tabview.add("底图与网络")

        self.scroll_base = ctk.CTkScrollableFrame(self.tab_base, fg_color="transparent")
        self.scroll_base.pack(fill="both", expand=True)
        self.scroll_visual = ctk.CTkScrollableFrame(self.tab_visual, fg_color="transparent")
        self.scroll_visual.pack(fill="both", expand=True)
        self.scroll_map = ctk.CTkScrollableFrame(self.tab_map, fg_color="transparent")
        self.scroll_map.pack(fill="both", expand=True)

        # --- 📍 Tab 1: 基础设置 ---
        self.add_section(self.scroll_base, "1. 数据源与目标")
        self.btn_excel = self.add_button(self.scroll_base, "选取业务数据 (Excel)", self.select_excel)
        self.sheet_var = tk.StringVar(value="等待读取...")
        self.sheet_menu = ctk.CTkOptionMenu(self.scroll_base, variable=self.sheet_var, values=["请先选文件"],
                                            state="disabled")
        self.sheet_menu.pack(pady=5, fill="x")

        last_dir = os.path.basename(self.cfg.get('last_dir', '')) if self.cfg.get('last_dir') else "未选择"
        self.btn_save_dir = self.add_button(self.scroll_base, f"保存至: {last_dir}", self.select_save_dir)

        self.filename_entry = ctk.CTkEntry(self.scroll_base, placeholder_text="输出图片名称")
        self.filename_entry.insert(0, f"Analysis_{time.strftime('%m%d_%H%M')}")
        self.filename_entry.pack(pady=5, fill="x")

        self.add_section(self.scroll_base, "2. 渲染质量与主题")
        self.dpi_menu = ctk.CTkOptionMenu(self.scroll_base, values=["200 (极速预览/Zoom10)", "400 (高清报告/Zoom11)",
                                                                    "600 (出版印刷/Zoom12)"])
        self.dpi_menu.set(self.cfg.get('dpi_str', "400 (高清报告/Zoom11)"))
        self.dpi_menu.pack(pady=5, fill="x")

        self.theme_menu = ctk.CTkOptionMenu(self.scroll_base, values=["经典绿黄红", "商务冷色蓝"])
        self.theme_menu.set(self.cfg.get('theme', "经典绿黄红"))
        self.theme_menu.pack(pady=5, fill="x")

        # --- 🎛️ Tab 2: 视觉与算法 ---
        self.add_section(self.scroll_visual, "1. 算法核心微调")
        self.sens_s = self.add_slider(self.scroll_visual, "红黄灵敏度 (Sens)", 1, 10, self.cfg.get('sens', 8.0))
        self.bw_s = self.add_slider(self.scroll_visual, "收束带宽 (bw)", 0.02, 0.15, self.cfg.get('bw', 0.06))
        self.thresh_s = self.add_slider(self.scroll_visual, "噪声过滤 (thresh)", 0.01, 0.30,
                                        self.cfg.get('thresh', 0.05))
        self.alpha_s = self.add_slider(self.scroll_visual, "整体不透明度 (Alpha)", 0.1, 1.0,
                                       self.cfg.get('alpha', 0.85))

        self.add_section(self.scroll_visual, "2. 视觉图层基础")
        self.sw_points = self.add_switch(self.scroll_visual, "置顶显示原始锚点", self.cfg.get('show_points', True))
        self.point_size_s = self.add_slider(self.scroll_visual, "锚点尺寸 (px)", 2, 40, self.cfg.get('point_size', 10))
        self.sw_colorbar = self.add_switch(self.scroll_visual, "生成右下角图例刻度",
                                           self.cfg.get('show_colorbar', True))
        self.sw_subway = self.add_switch(self.scroll_visual, "叠加原色地铁网线", self.cfg.get('show_subway', True))
        self.sw_names = self.add_switch(self.scroll_visual, "显示行政区名标注", self.cfg.get('show_names', True))
        self.sw_mask = self.add_switch(self.scroll_visual, "启用域外暗化遮罩", self.cfg.get('show_mask', True))
        self.mask_alpha_s = self.add_slider(self.scroll_visual, "背景遮罩深度", 0.1, 0.9,
                                            self.cfg.get('mask_alpha', 0.55))

        # ✨ 新增：高定版边界控制区 ✨
        self.add_section(self.scroll_visual, "3. 行政区划边界 (高定版)")
        self.sw_boundary = self.add_switch(self.scroll_visual, "开启区划边界线条", self.cfg.get('show_boundary', True))

        self.boundary_color_menu = ctk.CTkOptionMenu(
            self.scroll_visual,
            values=["深灰 (#444444)", "纯黑 (#000000)", "纯白 (#FFFFFF)", "科技蓝 (#00E5FF)", "预警红 (#FF3333)"]
        )
        self.boundary_color_menu.set(self.cfg.get('boundary_color', "深灰 (#444444)"))
        self.boundary_color_menu.pack(pady=4, fill="x")

        self.boundary_style_menu = ctk.CTkOptionMenu(
            self.scroll_visual,
            values=["标准虚线 (--)", "细密虚线 (:)", "点划线 (-.)", "强力实线 (-)"]
        )
        self.boundary_style_menu.set(self.cfg.get('boundary_style', "标准虚线 (--)"))
        self.boundary_style_menu.pack(pady=4, fill="x")

        self.boundary_width_s = self.add_slider(self.scroll_visual, "线条粗细权重", 0.5, 5.0,
                                                self.cfg.get('boundary_width', 1.0))
        self.boundary_alpha_s = self.add_slider(self.scroll_visual, "线条通透度", 0.1, 1.0,
                                                self.cfg.get('boundary_alpha', 0.6))

        # --- ⚙️ Tab 3: 底图与网络 ---
        self.add_section(self.scroll_map, "1. 底图源选择")
        self.basemap_menu = ctk.CTkOptionMenu(
            self.scroll_map,
            values=[
                "GeoQ极简灰 (国内/极速/推荐)", "GeoQ藏青蓝 (国内/极速/夜间)",
                "高德标准版 (国内/稳定)", "高德纯路网 (国内/无底色)",
                "CARTO无字极简 (海外/需代理)", "OSM开源街道 (海外/需代理)", "纯净白底 (无底图)"
            ],
            command=self.refresh_cache_status
        )
        self.basemap_menu.set(self.cfg.get('basemap', "GeoQ极简灰 (国内/极速/推荐)"))
        self.basemap_menu.pack(pady=5, fill="x")

        self.add_section(self.scroll_map, "2. 网络与代理")
        self.sw_proxy = self.add_switch(self.scroll_map, "开启本地局域网代理", self.cfg.get('use_proxy', False))
        self.proxy_port_entry = ctk.CTkEntry(self.scroll_map, placeholder_text="代理端口 (默认 7890)")
        self.proxy_port_entry.insert(0, self.cfg.get('proxy_port', "7890"))
        self.proxy_port_entry.pack(pady=4, fill="x")

        self.add_section(self.scroll_map, "3. 离线缓存池管理")
        self.zoom_menu = ctk.CTkOptionMenu(
            self.scroll_map,
            values=["Zoom 10 (街道梗概/极速)", "Zoom 11 (路网细节/推荐)", "Zoom 12 (建筑轮廓/极清)"],
            command=self.refresh_cache_status
        )
        self.zoom_menu.set(self.cfg.get('zoom_str', "Zoom 11 (路网细节/推荐)"))
        self.zoom_menu.pack(pady=5, fill="x")

        self.lbl_cache_status = ctk.CTkLabel(self.scroll_map, text="扫描中...", font=ctk.CTkFont(weight="bold"))
        self.lbl_cache_status.pack(pady=(5, 10))

        self.btn_download_map = ctk.CTkButton(
            self.scroll_map, text="⬇️ 获取/补全所选精度图源",
            fg_color="#34A853", hover_color="#2B8C46", font=ctk.CTkFont(weight="bold"),
            command=self.trigger_map_download
        )
        self.btn_download_map.pack(pady=(5, 15), fill="x")

        # ================= 左侧底部：常驻执行区 =================
        self.bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 20))

        self.prog = ctk.CTkProgressBar(self.bottom_frame, mode="indeterminate", height=6)
        self.prog.pack(fill="x", pady=(0, 10))
        self.prog.set(0)

        self.run_btn = ctk.CTkButton(
            self.bottom_frame, text="🚀 开始执行空间渲染", height=50,
            font=ctk.CTkFont(size=16, weight="bold"), command=self.start_task
        )
        self.run_btn.pack(fill="x")

        # ================= UI 右侧：控制台 =================
        self.content = ctk.CTkFrame(self, fg_color="#F8F9FA")
        self.content.grid(row=0, column=1, padx=(10, 30), pady=30, sticky="nsew")

        ctk.CTkLabel(self.content, text="运行状态与控制台日志", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(0, 10))

        self.log_box = ctk.CTkTextbox(self.content, font=("Consolas", 13), border_width=1)
        self.log_box.pack(fill="both", expand=True)
        self.log_box.insert("end", "引擎加载完毕。支持底图断网缓存。等待下达指令...\n\n")

        self.refresh_cache_status()

    # ================= UI 组件辅助 =================
    def add_section(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"), text_color="#1A73E8").pack(
            pady=(15, 5), anchor="w")

    def add_button(self, parent, text, cmd):
        btn = ctk.CTkButton(parent, text=text, command=cmd, fg_color="#F1F3F4", text_color="#3C4043")
        btn.pack(pady=4, fill="x")
        return btn

    def add_switch(self, parent, text, default):
        var = tk.BooleanVar(value=default)
        ctk.CTkSwitch(parent, text=text, variable=var).pack(pady=4, fill="x")
        return var

    def add_slider(self, parent, text, min_v, max_v, def_v):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=2)
        lbl_f = ctk.CTkFrame(f, fg_color="transparent")
        lbl_f.pack(fill="x")
        ctk.CTkLabel(lbl_f, text=text, font=("Arial", 12)).pack(side="left")
        v_lbl = ctk.CTkLabel(lbl_f, text=f"{def_v:.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#1A73E8")
        v_lbl.pack(side="right")
        s = ctk.CTkSlider(f, from_=min_v, to=max_v, command=lambda v: v_lbl.configure(text=f"{v:.2f}"))
        s.set(def_v)
        s.pack(fill="x")
        return s

    # ================= 逻辑交互 =================
    def gather_current_configs(self):
        return {
            "use_proxy": self.sw_proxy.get(),
            "proxy_port": self.proxy_port_entry.get().strip(),
            "last_dir": self.cfg.get('last_dir', ''),
            "basemap": self.basemap_menu.get(),
            "zoom_str": self.zoom_menu.get(),
            "sens": self.sens_s.get(), "bw": self.bw_s.get(),
            "thresh": self.thresh_s.get(), "alpha": self.alpha_s.get(),
            "show_points": self.sw_points.get(), "point_size": self.point_size_s.get(),
            "show_colorbar": self.sw_colorbar.get(), "show_subway": self.sw_subway.get(),
            "show_names": self.sw_names.get(), "show_mask": self.sw_mask.get(),
            "mask_alpha": self.mask_alpha_s.get(), "theme": self.theme_menu.get(),
            "dpi_str": self.dpi_menu.get(),

            # ✨ 新增：高定边界参数透传 ✨
            "show_boundary": self.sw_boundary.get(),
            "boundary_color": self.boundary_color_menu.get(),
            "boundary_style": self.boundary_style_menu.get(),
            "boundary_width": self.boundary_width_s.get(),
            "boundary_alpha": self.boundary_alpha_s.get()
        }

    def select_excel(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if p:
            self.excel_path = p
            self.btn_excel.configure(text=f"✅ {os.path.basename(p)}")
            sheets = pd.ExcelFile(p).sheet_names
            self.sheet_menu.configure(values=sheets, state="normal")
            self.sheet_var.set(sheets[0])

    def select_save_dir(self):
        d = filedialog.askdirectory(initialdir=self.cfg.get('last_dir', ''))
        if d:
            self.cfg['last_dir'] = d
            self.btn_save_dir.configure(text=f"📁 {os.path.basename(d)}")

    def log_update(self, msg):
        self.after(0, lambda: self.log_box.insert("end", f"{msg}\n"))
        self.after(0, lambda: self.log_box.see("end"))

    def refresh_cache_status(self, _=None):
        basemap = self.basemap_menu.get()
        zoom_str = self.zoom_menu.get()
        zoom = int(zoom_str.split(" ")[1])

        pct = canvas.get_cache_status(basemap, zoom)

        if pct == 1.0:
            self.lbl_cache_status.configure(text="🟢 当前状态: 已完整缓存 (支持秒出)", text_color="#2B8C46")
        elif pct == 0.0:
            self.lbl_cache_status.configure(text="🔴 当前状态: 未缓存 (需联网下载)", text_color="#EA4335")
        else:
            self.lbl_cache_status.configure(text=f"🟡 当前状态: 缓存不完整 ({pct * 100:.1f}%)", text_color="#F9AB00")

    def action_cancel_download(self):
        self._cancel_download_flag = True
        self.btn_download_map.configure(state="disabled", text="🛑 正在强制刹车...")
        self.log_update("⚠️ [急停指令] 已下达，网络通讯切断中...")

    def check_cancel_callback(self):
        return self._cancel_download_flag

    def trigger_map_download(self):
        self._cancel_download_flag = False
        current_state = self.gather_current_configs()
        save_config(self.config_path, current_state)
        self.cfg = current_state

        params_for_download = self.cfg.copy()
        params_for_download['zoom_level'] = int(self.cfg['zoom_str'].split(" ")[1])

        self.btn_download_map.configure(
            state="normal",
            text="🛑 中止并保存当前进度",
            fg_color="#D32F2F", hover_color="#B71C1C",
            command=self.action_cancel_download
        )
        self.run_btn.configure(state="disabled")
        self.prog.configure(mode="determinate")
        self.prog.set(0.0)

        self.lbl_cache_status.configure(text="🟡 当前状态: 正在高速拉取...", text_color="#F9AB00")

        self.log_update("\n" + "=" * 50)
        self.log_update(f"📥 正在扫描并补全 {self.cfg['basemap']} - Zoom {params_for_download['zoom_level']} ...")

        threading.Thread(target=self.worker_download, args=(params_for_download,), daemon=True).start()

    def progress_callback(self, current, total):
        pct = current / total
        self.after(0, lambda: self.prog.set(pct))
        self.after(0, lambda: self.btn_download_map.configure(
            text=f"🛑 中止下载 ({pct * 100:.1f}%)") if not self._cancel_download_flag else None)

        if current % 20 == 0:
            self.after(0, self.refresh_cache_status)

    def worker_download(self, params):
        success = canvas.download_cache(params, self.log_update, self.progress_callback, self.check_cancel_callback)
        self.after(0, self.finish_download, success)

    def finish_download(self, success):
        self.btn_download_map.configure(
            state="normal",
            text="⬇️ 获取/补全所选精度图源",
            fg_color="#34A853", hover_color="#2B8C46",
            command=self.trigger_map_download
        )
        self.run_btn.configure(state="normal")
        self.prog.configure(mode="indeterminate")
        self.prog.stop()

        self.refresh_cache_status()

        if success: messagebox.showinfo("任务完成", "底图离线包已补全并锁定！")

    def start_task(self):
        if not hasattr(self, 'excel_path'):
            messagebox.showwarning("验证失败", "请优先配置业务 Excel 数据表源！")
            self.tabview.set("基础设置")
            return

        current_state = self.gather_current_configs()
        save_config(self.config_path, current_state)
        self.cfg = current_state

        self.run_btn.configure(state="disabled", text="引擎流水线运转中...")
        self.btn_download_map.configure(state="disabled")
        self.prog.configure(mode="indeterminate")
        self.prog.start()

        params = self.cfg.copy()
        params['zoom_level'] = int(self.cfg.get('zoom_str', "Zoom 11").split(" ")[1])
        params.update({
            'excel': self.excel_path, 'sheet': self.sheet_var.get(),
            'out_dir': self.cfg.get('last_dir', ''), 'filename': self.filename_entry.get(),
            'dpi': int(self.dpi_menu.get().split(" ")[0])
        })

        threading.Thread(target=self.worker, args=(params,), daemon=True).start()

    def worker(self, params):
        success = HeatmapPipeline.execute(params, self.log_update)
        self.after(0, self.finish_task, success)

    def finish_task(self, success):
        self.run_btn.configure(state="normal", text="🚀 开始执行空间渲染")
        self.btn_download_map.configure(state="normal")
        self.prog.stop()

        self.refresh_cache_status()

        if success: messagebox.showinfo("渲染就绪", f"分析报告已生成并保存至：\n{self.cfg.get('last_dir', '')}")

    def on_closing(self):
        save_config(self.config_path, self.gather_current_configs())
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()