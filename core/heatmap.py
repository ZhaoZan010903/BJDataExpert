import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


def run(ax, gdf_wm, params, log_callback):
    """
    第三步：执行 KDE (核密度估计) 计算并渲染热力涂层。
    返回: 动态生成的 Colormap (供后续图例使用)
    """
    log_callback(f"| [3/6] 执行空间密度权重分布计算...")

    sens = params['sens']
    # 动态推算色彩节点，灵敏度越高，高危色(红/深蓝)扩散越广
    y_node = max(0.01, 0.28 / (sens ** 1.1))
    r_node = max(0.04, 0.80 / (sens ** 1.1))

    # 根据主题构建渐变色带
    if params['theme'] == "经典绿黄红":
        colors = [(0.0, (1, 1, 1, 0)), (0.01, '#84ff00'), (y_node, '#ffeb00'), (r_node, '#ff0000'), (1.0, '#7a0000')]
    else:
        colors = [(0.0, (1, 1, 1, 0)), (0.01, '#ebf5ff'), (y_node, '#6baed6'), (r_node, '#2171b5'), (1.0, '#08306b')]

    cmap = LinearSegmentedColormap.from_list('DynHeat', colors)

    # 核心算法：通过 Seaborn 渲染核密度表面
    sns.kdeplot(
        x=gdf_wm.geometry.x, y=gdf_wm.geometry.y, ax=ax, cmap=cmap, fill=True,
        bw_adjust=params['bw'], thresh=params['thresh'], levels=60, alpha=params['alpha'], zorder=2
    )

    return cmap