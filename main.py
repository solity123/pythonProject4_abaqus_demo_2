import os
import time
import shutil
import sys
from de_algorithm import de
from config import (
    ORIGINAL_INP,
    TEMPLATE_FILE,
    POP_SIZE,
    GENERATIONS,
    F,
    CR,
    PARALLEL,
    RESULT_DIR,
    OPTIMIZATION_TARGET,
    OPTIMIZATION_DIRECTION,
    PROJECT_ROOT,
    update_bounds
)
from template_parser import TemplateParser
from inp_editor import INPEditor
from abaqus_util import abaqus_objective
import multiprocessing as mp


if __name__ == '__main__':
    mp.freeze_support()


def clean_result_folder():
    """清理结果目录"""
    if os.path.exists(RESULT_DIR):
        print(f"🧹 清理结果目录: {RESULT_DIR}")
        for item in os.listdir(RESULT_DIR):
            item_path = os.path.join(RESULT_DIR, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️ 清理失败: {item_path} - {str(e)}")
    else:
        os.makedirs(RESULT_DIR, exist_ok=True)
        print(f"📁 创建结果目录: {RESULT_DIR}")


def create_template():
    """创建模板文件"""
    original_path = os.path.join(PROJECT_ROOT, ORIGINAL_INP)
    template_path = os.path.join(PROJECT_ROOT, TEMPLATE_FILE)

    if not os.path.exists(original_path):
        print(f"❌ 原始INP文件不存在: {original_path}")
        print("请将Abaqus生成的INP文件保存为 'demo.inp'")
        return None, []

    print("🛠️ 启动交互式模板编辑器...")
    editor = INPEditor()
    suggested_bounds = editor.interactive_edit()
    if not suggested_bounds:
        print("❌ 模板创建取消")
        return None, []

    return template_path, suggested_bounds


def apply_optimization_direction(value):
    """根据优化方向调整目标值"""
    if OPTIMIZATION_DIRECTION == "max":
        return -value  # 最大化转换为最小化问题
    return value


# def create_objective_function(template_parser):
#     """创建可序列化的目标函数"""
#     def wrapped_objective(x):
#         return apply_optimization_direction(
#             abaqus_objective(x, template_parser)
#         )
#     return wrapped_objective
# 在 main.py 中添加
class ObjectiveFunction:
    """可序列化的目标函数类"""

    def __init__(self, template_parser):
        self.template_parser = template_parser

    def __call__(self, x):
        return apply_optimization_direction(
            abaqus_objective(x, self.template_parser)
        )


def main():
    """主优化流程"""
    # 初始化环境
    clean_result_folder()

    # 创建模板并获取边界建议
    template_path, suggested_bounds = create_template()
    if not template_path or not suggested_bounds:
        print("❌ 优化准备失败")
        return

    # 更新边界配置
    update_bounds(suggested_bounds)

    # 初始化模板解析器
    template_parser = TemplateParser()
    try:
        template_parser.load_template()
        param_count = template_parser.get_parameters_count()
        print(f"🔧 模板包含 {param_count} 个优化参数")
    except Exception as e:
        print(f"❌ 模板加载失败: {str(e)}")
        return

    start_time = time.time()

    print("\n" + "=" * 60)
    print(f"🚀 启动参数优化 | 目标: {OPTIMIZATION_DIRECTION} {OPTIMIZATION_TARGET}")
    print(f"🔢 参数空间: {suggested_bounds}")
    print(f"🧬 DE算法: {POP_SIZE}种群/{GENERATIONS}代 | F={F} CR={CR}")
    print("=" * 60 + "\n")

    try:
        # 创建可序列化的目标函数
        # objective_func = create_objective_function(template_parser)
        objective_func = ObjectiveFunction(template_parser)
        # 运行优化算法
        best_x, best_f = de(
            objective_func=objective_func,
            bounds=suggested_bounds,
            pop_size=POP_SIZE,
            gens=GENERATIONS,
            F=F,
            CR=CR,
            parallel=PARALLEL
        )

        # 调整最终结果方向
        final_fitness = best_f if OPTIMIZATION_DIRECTION == "min" else -best_f

        # 输出最终结果
        print("\n" + "=" * 60)
        print(f"✅ 优化完成! 耗时: {time.time() - start_time:.2f}秒")
        print(f"🏆 最优参数: {best_x}")
        print(f"🎯 最优目标值: {final_fitness:.6f}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 优化过程失败: {str(e)}")
        import traceback
        traceback.print_exc()

    except KeyboardInterrupt:
        print("Program interrupted by user")


if __name__ == "__main__":
    main()


