import subprocess
import os
import time
import uuid
import shutil
from config import (
    ABAQUS_COMMAND,
    ABAQUS_TIMEOUT,
    RESULT_DIR,
    OPTIMIZATION_TARGET,
    NODE_LABEL,
    PROJECT_ROOT
)


def run_abaqus(run_dir, job_name, timeout=ABAQUS_TIMEOUT):
    """运行Abaqus作业"""
    os.makedirs(run_dir, exist_ok=True)

    # 检查INP文件是否存在
    inp_path = os.path.join(run_dir, f"{job_name}.inp")
    if not os.path.isfile(inp_path):
        print(f"❌ 未找到INP文件: {inp_path}")
        return False, None

    # 构建Abaqus命令
    command = f"{ABAQUS_COMMAND} job={job_name} input={job_name}.inp interactive cpus=1 mp_mode=threads"
    print(f"▶ 正在运行Abaqus: {command} @ {run_dir}")

    try:
        # 执行Abaqus命令
        result = subprocess.run(
            command,
            shell=True,
            cwd=run_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )

        # 检查执行结果
        if result.returncode != 0:
            # 打印完整的错误信息
            error_msg = result.stderr.decode(errors='ignore')
            print(f"❌ Abaqus执行失败 (code={result.returncode}):")
            print(error_msg[:500])  # 打印前500个字符的错误信息

            # 尝试读取日志文件获取更多错误信息
            log_path = os.path.join(run_dir, f"{job_name}.log")
            if os.path.exists(log_path):
                with open(log_path, 'r', errors='ignore') as log_file:
                    log_content = log_file.read(500)  # 读取前500个字符
                    print(f"📝 日志文件内容 (前500字符):")
                    print(log_content)
            return False, None

        # 验证ODB文件
        odb_path = os.path.join(run_dir, f"{job_name}.odb")
        if not os.path.isfile(odb_path):
            print(f"❌ Abaqus运行成功但未生成ODB文件: {odb_path}")
            return False, None

        return True, odb_path

    except subprocess.TimeoutExpired:
        print(f"⏱️ Abaqus执行超时 ({timeout}秒)")
        return False, None

    except Exception as e:
        print(f"❌ 运行Abaqus时发生异常: {str(e)}")
        return False, None


def parse_result_from_odb(odb_path):
    """通过Abaqus Python环境解析ODB文件"""
    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser_script = os.path.join(script_dir, "parse_odb.py")

    # 构建命令 - 添加完整路径确保可执行
    cmd = f"{ABAQUS_COMMAND} python \"{parser_script}\" \"{odb_path}\" {OPTIMIZATION_TARGET} {NODE_LABEL}"

    print(f"🔍 解析ODB文件: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        # 不需要手动解码，因为使用 PIPE 返回的是字节
        stdout = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            print(f"❌ ODB解析失败 (code={result.returncode}):")

            # 尝试解码错误信息
            try:
                stderr_str = stderr.decode('utf-8', errors='replace')
                print(f"标准错误输出:\n{stderr_str}")
            except:
                print(f"标准错误输出 (原始字节):\n{stderr}")

            # 尝试解码标准输出
            try:
                stdout_str = stdout.decode('utf-8', errors='replace')
                print(f"标准输出:\n{stdout_str}")
            except:
                print(f"标准输出 (原始字节):\n{stdout}")

            return float('inf')

        # 提取结果
        try:
            # 尝试解码输出
            output = stdout.decode('utf-8', errors='replace').strip()
            print(f"ODB解析输出: {output}")
            return float(output)
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                output = stdout.decode('gbk', errors='replace').strip()
                print(f"ODB解析输出 (GBK): {output}")
                return float(output)
            except:
                print(f"❌ 无法解码ODB输出: {stdout}")
                return float('inf')
        except ValueError:
            print(f"❌ 无法解析ODB输出为浮点数: {output}")
            return float('inf')

    except subprocess.TimeoutExpired:
        print(f"⏱️ ODB解析超时: {cmd}")
        return float('inf')

    except Exception as e:
        print(f"❌ ODB解析异常: {str(e)}")
        return float('inf')


def abaqus_objective(x, template_parser):
    """Abaqus目标函数（被DE算法调用）"""
    job_id = f"job_{int(time.time() * 1000)}_{uuid.uuid4().hex[:4]}"
    job_name = job_id
    run_dir = os.path.join(RESULT_DIR, job_id)

    try:
        # 生成INP文件
        inp_path = template_parser.write_inp(x, run_dir, job_name)
        print(f"📄 生成INP文件: {inp_path} | 参数: {x}")

        # 运行Abaqus
        success, obd_path = run_abaqus(run_dir, job_name)
        if not success or not obd_path:
            print(f"⚠️ 仿真失败: {job_name}")
            return float('inf')

        # 解析结果
        result = parse_result_from_odb(obd_path)
        print(f"📊 仿真结果: {result:.6f} | 参数: {x}")
        return result

    except Exception as e:
        print(f"❌ 目标函数执行失败: {str(e)}")
        return float('inf')