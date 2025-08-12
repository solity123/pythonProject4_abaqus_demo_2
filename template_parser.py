import os
import re
from config import PROJECT_ROOT, TEMPLATE_FILE, RESULT_DIR


class TemplateParser:
    def __init__(self):
        # 修正正则表达式以匹配 ${param} 格式
        self.param_pattern = r"\${(\w+)}"
        self.param_map = {}
        self.template_content = ""
        self.template_path = os.path.join(PROJECT_ROOT, TEMPLATE_FILE)
        self._loaded = False

    def load_template(self):
        """加载模板文件"""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"模板文件不存在: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()

        # 打印模板内容前20行用于调试
        print("\n🔍 加载模板文件内容 (前20行):")
        lines = self.template_content.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"{i + 1:3d} | {line}")

        self._identify_parameters()
        self._loaded = True

    def _identify_parameters(self):
        """识别模板中的参数占位符"""
        matches = re.findall(self.param_pattern, self.template_content)
        if not matches:
            print("⚠ 模板文件中未找到参数占位符 (格式: ${param_name})")
            return

        unique_params = list(set(matches))
        print(f"🔍 识别到 {len(unique_params)} 个优化参数: {', '.join(unique_params)}")
        self.param_map = {param: f"${param}" for param in unique_params}
        return unique_params

    def get_parameters(self):
        """获取参数列表"""
        if not self._loaded:
            self.load_template()
        return list(self.param_map.keys())

    def get_parameters_count(self):
        """获取参数数量"""
        if not self._loaded:
            self.load_template()
        return len(self.param_map)

    def write_inp(self, parameters, job_dir, job_name):
        """根据参数生成INP文件"""
        if not self._loaded:
            self.load_template()

        if not self.param_map:
            raise ValueError("模板中没有可替换的参数")

        param_count = len(self.param_map)
        if len(parameters) != param_count:
            raise ValueError(
                f"参数数量不匹配: 模板需要 {param_count} 个参数, "
                f"实际提供 {len(parameters)} 个"
            )

        content = self.template_content
        param_names = list(self.param_map.keys())

        # 确保参数按顺序替换
        for i, param_name in enumerate(param_names):
            placeholder = self.param_map[param_name]
            # 使用完整的 ${param} 格式进行替换
            content = content.replace(f"${{{param_name}}}", f"{parameters[i]:.6f}")

        os.makedirs(job_dir, exist_ok=True)
        inp_path = os.path.join(job_dir, f"{job_name}.inp")

        with open(inp_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 打印生成的INP文件前10行用于调试
        print("\n📄 生成的INP文件内容 (前10行):")
        lines = content.split('\n')
        for i, line in enumerate(lines[:10]):
            print(f"{i + 1:3d} | {line}")

        return inp_path

    def __getstate__(self):
        """用于序列化"""
        state = self.__dict__.copy()
        # 移除不能序列化的属性
        state.pop('template_content', None)
        return state

    def __setstate__(self, state):
        """用于反序列化"""
        self.__dict__.update(state)
        # 重新加载模板内容
        self.load_template()