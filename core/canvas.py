import os
import time
import shutil
import urllib.request
import requests
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import contextily as cx
import mercantile
from config_manager import get_user_data_path

# ================= 🚀 终极防封禁反爬与防死锁补丁 =================
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'),
                     ('Accept', 'image/webp,image/apng,image/*,*/*;q=0.8')]
urllib.request.install_opener(opener)

_original_request = requests.Session.request


def _patched_request(self, method, url, **kwargs):
    headers = kwargs.get('headers', {})
    if headers is None: headers = {}
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'
    if 'autonavi.com' in url or 'amap.com' in url:
        headers['Referer'] = 'https://www.amap.com/'
    elif 'geoq.cn' in url:
        headers['Referer'] = 'https://map.geoq.cn/'
    elif 'carto' in url or 'osm' in url:
        headers['Referer'] = 'https://www.openstreetmap.org/'
    kwargs['headers'] = headers
    # 💡 核心修复：强制加入3秒超时，防止网络死锁导致无法取消下载！
    kwargs['timeout'] = 3.0
    return _original_request(self, method, url, **kwargs)


requests.Session.request = _patched_request
# =================================================================

SOURCES_MAP = {
    "GeoQ极简灰 (国内/极速/推荐)": "https://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetGray/MapServer/tile/{z}/{y}/{x}",
    "GeoQ藏青蓝 (国内/极速/夜间)": "https://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}",
    "高德标准版 (国内/稳定)": "https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=7",
    "高德纯路网 (国内/无底色)": "https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=8",
    "CARTO无字极简 (海外/需代理)": cx.providers.CartoDB.VoyagerNoLabels,
    "OSM开源街道 (海外/需代理)": cx.providers.OpenStreetMap.Mapnik,
    "纯净白底 (无底图)": None
}

CACHE_FOLDERS = {
    "GeoQ极简灰 (国内/极速/推荐)": "geoq_gray",
    "GeoQ藏青蓝 (国内/极速/夜间)": "geoq_blue",
    "高德标准版 (国内/稳定)": "gaode_std",
    "高德纯路网 (国内/无底色)": "gaode_road",
    "CARTO无字极简 (海外/需代理)": "carto_voyager",
    "OSM开源街道 (海外/需代理)": "osm_mapnik"
}


def setup_proxy(params, log_callback):
    use_proxy = params.get('use_proxy', False)
    proxy_port = params.get('proxy_port', "7890")
    if use_proxy and proxy_port:
        proxy_url = f"http://127.0.0.1:{proxy_port}"
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        log_callback(f"| 🌍 已挂载代理: {proxy_url}")
        return True
    return False


def clear_proxy():
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)


def get_beijing_bounds():
    bj_bbox = gpd.GeoDataFrame(geometry=[Point(115.416, 39.450), Point(117.500, 41.050)], crs="EPSG:4326")
    bj_bbox_3857 = bj_bbox.to_crs(epsg=3857)
    minx, miny, maxx, maxy = bj_bbox_3857.total_bounds
    return minx, miny, maxx, maxy, bj_bbox_3857.crs.to_string()


def get_cache_dir_by_zoom(selected_style, zoom_level):
    folder_name = CACHE_FOLDERS.get(selected_style, "other_maps")
    return get_user_data_path(os.path.join("map_cache", folder_name, f"zoom_{zoom_level}"))


# 💡 核心修复：硬盘实地雷达扫描 (修正扩展名误判，引入证书优先机制)
def get_cache_status(selected_style, zoom_level):
    if not selected_style or selected_style == "纯净白底 (无底图)":
        return 1.0  # 100% 缓存

    cache_dir = get_cache_dir_by_zoom(selected_style, zoom_level)
    if not os.path.exists(cache_dir):
        return 0.0

    # 【修复1】只要文件夹里有这本“完工证书”，就代表上一次 100% 拉取成功了，直接亮绿灯！
    ts_file = os.path.join(cache_dir, "last_check.txt")
    if os.path.exists(ts_file):
        return 1.0

        # 【修复2】如果没有证书（比如下载了一半被你急停了），再去数真实文件数
    tiles = list(mercantile.tiles(115.416, 39.450, 117.500, 41.050, zooms=zoom_level))
    expected = len(tiles)
    if expected == 0: return 0.0

    # Contextily 生成的瓦片很多没有后缀，所以我们只剔除掉 .txt，剩下的全算作瓦片图片
    actual = len([f for f in os.listdir(cache_dir) if not f.endswith('.txt')])

    return min(actual / expected, 1.0)

def write_timestamp(cache_dir):
    ts_file = os.path.join(cache_dir, "last_check.txt")
    try:
        with open(ts_file, "w") as f:
            f.write(str(time.time()))
    except:
        pass


def check_timestamp(cache_dir):
    ts_file = os.path.join(cache_dir, "last_check.txt")
    if os.path.exists(ts_file):
        try:
            if time.time() - float(open(ts_file, "r").read()) < 259200:
                return False
        except:
            pass
    return True


def execute_smart_download(map_source, zoom_level, cache_dir, log_callback, progress_callback=None,
                           cancel_callback=None):
    cx.set_cache_dir(cache_dir)
    tiles = list(mercantile.tiles(115.416, 39.450, 117.500, 41.050, zooms=zoom_level))
    total_tiles = len(tiles)
    tiles_to_download = tiles
    max_rounds = 3

    for round_idx in range(max_rounds):
        failed_tiles = []
        for i, tile in enumerate(tiles_to_download):

            # 🛑 秒级安全中断响应
            if cancel_callback and cancel_callback():
                log_callback("🛑 [安全中断] 已紧急刹车，保护现有硬盘缓存不被破坏。")
                return False

            bounds = mercantile.bounds(tile)
            lng = (bounds.west + bounds.east) / 2
            lat = (bounds.south + bounds.north) / 2

            tile_success = False
            for attempt in range(3):
                try:
                    cx.bounds2img(lng - 0.0001, lat - 0.0001, lng + 0.0001, lat + 0.0001,
                                  zoom=zoom_level, source=map_source, ll=True)
                    tile_success = True
                    break
                except Exception as e:
                    time.sleep(0.5)

            if not tile_success: failed_tiles.append(tile)

            # 实时进度条
            if progress_callback and round_idx == 0: progress_callback(i + 1, total_tiles)

        if not failed_tiles: break

        if failed_tiles and round_idx < max_rounds - 1:
            log_callback(f"⚠️ 第 {round_idx + 1} 轮有 {len(failed_tiles)} 张拉取失败。放入队尾重试...")
            time.sleep(1)
            tiles_to_download = failed_tiles

    if failed_tiles:
        log_callback(f"❌ 经过硬核重试，仍有 {len(failed_tiles)} 张拉取失败。")
        return False
    else:
        log_callback("✅ 高清瓦片矩阵已100%完整就绪！")
        write_timestamp(cache_dir)
        return True


def download_cache(params, log_callback, progress_callback=None, cancel_callback=None):
    selected_style = params.get('basemap', "GeoQ极简灰 (国内/极速/推荐)")
    map_source = SOURCES_MAP.get(selected_style)
    if not map_source: return False

    zoom_level = params.get('zoom_level', 11)
    cache_dir = get_cache_dir_by_zoom(selected_style, zoom_level)

    # 💡 保留现有缓存，不要粗暴全删，实现“查漏补缺式”下载
    os.makedirs(cache_dir, exist_ok=True)

    log_callback(f"⏳ 开始拉取底图 [{selected_style}] (专属精度: Zoom {zoom_level})")
    proxy_used = setup_proxy(params, log_callback)
    try:
        success = execute_smart_download(map_source, zoom_level, cache_dir, log_callback, progress_callback,
                                         cancel_callback)
        return success
    finally:
        if proxy_used: clear_proxy()


def run(gdf_wm, params, log_callback):
    fig, ax = plt.subplots(figsize=(24, 20))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    minx, miny, maxx, maxy, crs_str = get_beijing_bounds()
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    selected_style = params.get('basemap', "GeoQ极简灰 (国内/极速/推荐)")
    map_source = SOURCES_MAP.get(selected_style)

    if map_source is not None:
        # 💡 核心修复：生图时，严格遵循 DPI 决定 Zoom 的法则！彻底无视 Tab 3！
        dpi = params.get('dpi', 400)
        zoom_level = 10 if dpi <= 200 else (11 if dpi <= 400 else 12)

        cache_dir = get_cache_dir_by_zoom(selected_style, zoom_level)
        os.makedirs(cache_dir, exist_ok=True)

        # 自动查缺补漏
        if check_timestamp(cache_dir) or get_cache_status(selected_style, zoom_level) < 1.0:
            log_callback(f"| [2/6] ⏳ 当前精度(Zoom {zoom_level})不完整，启动静默查漏补缺...")
            proxy_used = setup_proxy(params, log_callback)
            try:
                execute_smart_download(map_source, zoom_level, cache_dir, log_callback)
            except Exception as e:
                pass
            finally:
                if proxy_used: clear_proxy()

        folder_name = os.path.basename(os.path.dirname(cache_dir))
        log_callback(f"| [2/6] 正在接驳专属缓存目录: {folder_name}/zoom_{zoom_level}...")
        proxy_used = setup_proxy(params, log_callback)
        try:
            cx.set_cache_dir(cache_dir)
            cx.add_basemap(ax, crs=crs_str, source=map_source, zoom=zoom_level, zorder=1, alpha=0.9)
        except Exception as e:
            log_callback(f"| [2/6] ⚠️ 警告：底图渲染异常！错误信息: {e}")
        finally:
            if proxy_used: clear_proxy()
    else:
        log_callback(f"| [2/6] 用户选择无底图模式。")

    return fig, ax, (minx, miny, maxx, maxy)