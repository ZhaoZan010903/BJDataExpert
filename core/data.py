import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def run(params, log_callback):
    """
    第一步：加载并清洗 Excel 数据。
    返回: 转换坐标系后的 GeoDataFrame (gdf_wm)
    """
    log_callback(f"| [1/6] 正在读取并解析 Excel 数据源...")

    df = pd.read_excel(params['excel'], sheet_name=params['sheet'])
    df.columns = [c.strip() for c in df.columns]

    raw_count = len(df)
    # 强制转换坐标格式，过滤异常值
    df['经度'] = pd.to_numeric(df['经度'], errors='coerce')
    df['纬度'] = pd.to_numeric(df['纬度'], errors='coerce')
    df = df.dropna(subset=['经度', '纬度'])

    # 粗略截取北京及其周边范围的有效坐标
    df = df[(df['经度'] >= 115.0) & (df['经度'] <= 118.0) & (df['纬度'] >= 39.0) & (df['纬度'] <= 42.0)]
    valid_count = len(df)

    log_callback(
        f"| >> 原始条目: {raw_count} | 有效坐标: {valid_count} | 清洗率: {((raw_count - valid_count) / raw_count * 100) if raw_count else 0:.1f}%")

    # 组装点位几何信息，并将 WGS84(4326) 投影转换为 Web 墨卡托(3857) 以适配高德底图
    gdf_wm = gpd.GeoDataFrame(
        df, geometry=[Point(xy) for xy in zip(df['经度'], df['纬度'])], crs="EPSG:4326"
    ).to_crs(epsg=3857)

    return gdf_wm