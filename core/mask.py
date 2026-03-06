import geopandas as gpd
from shapely.geometry import box
import matplotlib.patheffects as patheffects


def run(ax, bbox, params, log_callback):
    """
    第五步：拉取行政区划，应用域外暗化遮罩，动态绘制行政区边界，并绘制带描边的区名。
    """
    log_callback("| [5/6] 绘制行政区划、边界与域外遮罩...")
    minx, miny, maxx, maxy = bbox

    # 在线拉取北京区划数据
    bj_dist = gpd.read_file("https://geo.datav.aliyun.com/areas_v3/bound/110000_full.json").to_crs(epsg=3857)

    # 1. 绘制域外暗化遮罩
    if params.get('show_mask', True):
        mask_geom = box(minx, miny, maxx, maxy).difference(bj_dist.geometry.unary_union)
        gpd.GeoDataFrame(geometry=[mask_geom], crs="EPSG:3857").plot(
            ax=ax, facecolor='black', alpha=params.get('mask_alpha', 0.55), zorder=3
        )

    # 2. ✨ 高级定制：动态绘制行政区边界 ✨
    if params.get('show_boundary', True):
        # 智能提取 UI 传来的 Hex 颜色码 (例如从 "深灰 (#444444)" 中提取 "#444444")
        color_str = params.get('boundary_color', '深灰 (#444444)')
        edge_color = color_str.split('(')[-1].strip(')')

        # 智能提取 UI 传来的线型符号 (例如从 "标准虚线 (--)" 中提取 "--")
        style_str = params.get('boundary_style', '标准虚线 (--)')
        line_style = style_str.split('(')[-1].strip(')')

        bj_dist.plot(
            ax=ax,
            facecolor='none',  # 内部透明
            edgecolor=edge_color,  # 动态颜色
            linestyle=line_style,  # 动态线型
            linewidth=params.get('boundary_width', 1.0),  # 动态粗细
            alpha=params.get('boundary_alpha', 0.6),  # 动态透明度
            zorder=4  # 确保在遮罩之上
        )

    # 3. 绘制行政区名称标注
    if params.get('show_names', True):
        stroke = [patheffects.withStroke(linewidth=4, foreground='white')]
        for _, row in bj_dist.iterrows():
            if row['name']:
                c = row.geometry.centroid
                tx, ty = c.x, c.y

                # 微调核心区文字位置防止拥挤
                if row['name'] == '东城区':
                    tx += 1500
                elif row['name'] == '西城区':
                    tx -= 1500

                txt = ax.text(tx, ty, row['name'], fontsize=18, fontweight='bold',
                              color='#111111', ha='center', va='center', zorder=8)
                txt.set_path_effects(stroke)