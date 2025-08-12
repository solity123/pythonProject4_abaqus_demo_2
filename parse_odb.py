import sys
import os


def main():
    if len(sys.argv) < 4:
        print("Usage: abaqus python parse_odb.py <odb_file> <metric> <node_label>")
        sys.exit(1)

    odb_file = sys.argv[1]
    metric = sys.argv[2]
    node_label = int(sys.argv[3])

    try:
        # 确保在Abaqus Python环境中
        from odbAccess import openOdb
        import numpy as np

        def get_max_displacement(odb_path, node_label=2):
            try:
                odb = openOdb(path=odb_path)

                # 获取第一个分析步
                step = next(iter(odb.steps.values()))
                if not step.frames:
                    print("⚠ 无帧数据，分析可能失败")
                    odb.close()
                    return float('inf')

                # 检查位移场
                frame = step.frames[-1]
                if 'U' not in frame.fieldOutputs:
                    print("⚠ 未输出位移场(U)")
                    odb.close()
                    return float('inf')

                # 查找指定节点的位移
                disp_field = frame.fieldOutputs['U']
                node_disp = None

                for value in disp_field.values:
                    if value.nodeLabel == node_label:
                        node_disp = value.data
                        break

                odb.close()

                if node_disp is None:
                    print(f"⚠ 节点 {node_label} 位移未找到")
                    return float('inf')

                return np.linalg.norm(node_disp)

            except Exception as e:
                print(f"❌ 解析位移时出错: {e}")
                return float('inf')

        def get_max_stress(odb_path):
            try:
                odb = openOdb(path=odb_path)

                # 获取第一个分析步
                step = next(iter(odb.steps.values()))
                if not step.frames:
                    print("⚠ 无帧数据，分析可能失败")
                    odb.close()
                    return float('inf')

                # 检查应力场
                frame = step.frames[-1]
                if 'S' not in frame.fieldOutputs:
                    print("⚠ 未输出应力场(S)")
                    odb.close()
                    return float('inf')

                # 计算最大Mises应力
                stress_field = frame.fieldOutputs['S']
                if stress_field.values is None:
                    print(f"⚠ 应力场数据为空")
                    return float('inf')

                max_stress = max([v.mises for v in stress_field.values])
                odb.close()
                return max_stress

            except Exception as e:
                print(f"❌ 解析应力时出错: {e}")
                return float('inf')

        def parse_odb_metric(odb_path, metric="max_stress", node=2):
            if metric == "max_disp":
                return get_max_displacement(odb_path, node_label=node)
            elif metric == "max_stress":
                return get_max_stress(odb_path)
            else:
                print(f"⚠ 未知指标类型: {metric}")
                return float('inf')

        result = parse_odb_metric(odb_file, metric, node_label)
        # print(result)
        sys.__stdout__.write(str(result))

    except ImportError:
        print("❌ 错误: 必须在 Abaqus Python 环境中运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
