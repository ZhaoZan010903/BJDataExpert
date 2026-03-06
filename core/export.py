import os
import matplotlib.pyplot as plt


def run(fig, ax, gdf_wm, cmap, params, log_callback):
    """
    第六步：绘制散点，生成内部图例，导出图片并清理内存。
    返回: 布尔值表示成功与否
    """
    # 置顶散点
    if params['show_points']:
        gdf_wm.plot(ax=ax, color='white', edgecolor='#111111', linewidth=0.6,
                    markersize=params['point_size'], alpha=1.0, zorder=10)

    # 生成右下角嵌入式图例
    if params['show_colorbar']:
        log_callback("| [图例] 生成右下角内部图例...")
        cax = ax.inset_axes([0.92, 0.05, 0.015, 0.25])
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
        cb = fig.colorbar(sm, cax=cax)

        cb.set_ticks([0.1, 0.5, 0.9])
        cb.set_ticklabels(['低密度区', '中密度区', '极高危核心'])

        # 图例文字颜色根据是否有黑色遮罩智能反转
        text_color = 'white' if params['show_mask'] else 'black'
        cb.ax.tick_params(colors=text_color, labelsize=14)
        cb.outline.set_visible(False)

        title_text = '高风险(红)' if params['theme'] == "经典绿黄红" else '高密度核心'
        cax.text(0.5, 1.05, title_text, transform=cax.transAxes, color=text_color,
                 ha='center', va='bottom', fontsize=16, fontweight='bold')

    log_callback(f"| [6/6] 引擎渲染中 (DPI: {params['dpi']})...")
    ax.set_axis_off()

    final_file = os.path.join(params['out_dir'], f"{params['filename']}.jpg")
    plt.savefig(final_file, format='jpg', bbox_inches='tight', pad_inches=0, dpi=params['dpi'])

    # 强制清理画板内存，防止多次运行后内存溢出
    plt.close(fig)
    return True