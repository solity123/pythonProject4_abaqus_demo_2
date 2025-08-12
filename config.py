import os

# ================ 文件配置 ================
ORIGINAL_INP = "try.inp"            # 原始INP文件(从Abaqus CAE生成)
TEMPLATE_FILE = "template.inp"        # 生成的模板文件

# ================ 优化配置 ================
# 边界配置将在模板创建后更新
BOUNDS = []  # 初始为空，模板创建后更新
OPTIMIZATION_TARGET = "max_disp"    # 优化目标: max_stress/max_disp
OPTIMIZATION_DIRECTION = "min"        # 优化方向: min/max
NODE_LABEL = 2                        # 位移分析节点

# ================ DE算法配置 ================
POP_SIZE = 4                          # 种群大小
GENERATIONS = 4                      # 迭代次数
F = 0.5                               # 缩放因子
CR = 0.9                              # 交叉概率
PARALLEL = True                       # 并行计算
MAX_CPU = 4                           # 最大并行进程数

# ================ ABAQUS配置 ================
ABAQUS_COMMAND = "abaqus"             # Abaqus命令
ABAQUS_TIMEOUT = 120                  # 运行超时(秒)
BASE_DIR = "result"                   # 结果目录

# ================ 自动配置 ================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RESULT_DIR = os.path.join(PROJECT_ROOT, BASE_DIR)


def update_bounds(new_bounds):
    """更新边界配置"""
    global BOUNDS
    BOUNDS = new_bounds
    print(f"✅ 已更新边界配置: {BOUNDS}")