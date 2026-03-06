import os
import json
import geopandas as gpd
from shapely.geometry import LineString
from config_manager import get_bundled_resource_path


def run(ax, params, log_callback):
    """
    第四步：解析本地 subway.json 并将地铁线网叠加到画布。
    无返回值，直接操作 ax 对象。
    """
    if not params['show_subway']:
        return

    local_json = get_bundled_resource_path("subway.json")
    if os.path.exists(local_json):
        log_callback("| [4/6] 识别到内嵌地铁线网数据，渲染中...")
        with open(local_json, 'r', encoding='utf-8') as f:
            sub_data = json.load(f)
            lines = []

            # 解析高德格式的地铁数据路线坐标
            for l in sub_data.get('l', []):
                coords = [list(map(float, st['sl'].split(','))) for st in l.get('st', []) if 'sl' in st]
                if len(coords) >= 2:
                    lines.append({'geometry': LineString(coords), 'color': f"#{l.get('cl', '999')}"})

            # 渲染线网
            if lines:
                sub_gdf = gpd.GeoDataFrame(lines, crs="EPSG:4326").to_crs(epsg=3857)
                sub_gdf.plot(ax=ax, color=sub_gdf['color'], linewidth=3.0, alpha=0.8, zorder=6)
    else:
        log_callback("| [4/6] ⚠️ 警告：未找到内嵌的 subway.json！跳过渲染。")