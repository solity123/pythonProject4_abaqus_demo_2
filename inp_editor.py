import os
import re
import sys


class INPEditor:
    def __init__(self):
        self.param_pattern = r"\${(\w+)}"
        self.param_map = {}
        self.lines = []
        self.param_counter = 1
        self.original_path = os.path.join(os.getcwd(), "try.inp")
        self.template_path = os.path.join(os.getcwd(), "template.inp")

        if not os.path.exists(self.original_path):
            raise FileNotFoundError(f"原始INP文件不存在: {self.original_path}")

    def load_file(self):
        """加载原始INP文件"""
        with open(self.original_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        print(f"📄 已加载INP文件: {self.original_path} ({len(self.lines)}行)")

    def display_lines(self, start=0, end=20):
        """显示文件内容片段，并显示字段序号"""
        print("\n" + "=" * 80)
        print(f"INP文件内容 (行 {start + 1}-{min(end, len(self.lines))}):")
        print("=" * 80)
        for i, line in enumerate(self.lines[start:end], start=start):
            # 显示行号和原始行内容
            line = line.rstrip()
            print(f"{i + 1:4d} | {line}")

            # 如果是数据行，显示字段序号
            if self.is_data_line(line):
                fields = self.parse_data_line(line)
                if fields:
                    print(f"     | 字段: " + ", ".join([f"[{j + 1}] {f}" for j, f in enumerate(fields)]))

    def is_data_line(self, line):
        """检查是否为数据行(包含逗号分隔的数字)"""
        # 更宽松的匹配规则，允许科学计数法、负数等
        return re.match(r'^\s*[\d\.,\s\-eE]+$', line) is not None

    def parse_data_line(self, line):
        """解析数据行中的数值字段"""
        # 移除行尾注释
        clean_line = re.sub(r',*\s*\*.*$', '', line).strip()
        if not clean_line:
            return []

        # 分割字段
        fields = [field.strip() for field in clean_line.split(',')]
        return fields

    def parameterize(self, line_num, field_num):
        """参数化指定位置"""
        try:
            line_idx = int(line_num) - 1
            field_idx = int(field_num) - 1

            if line_idx < 0 or line_idx >= len(self.lines):
                print(f"❌ 无效行号: {line_num}")
                return False

            line = self.lines[line_idx].rstrip()

            # 解析数据行
            fields = self.parse_data_line(line)
            if not fields:
                print(f"❌ 第 {line_num} 行没有可参数化的数值字段")
                return False

            if field_idx < 0 or field_idx >= len(fields):
                print(f"❌ 无效字段序号: {field_num} (最大 {len(fields)})")
                return False

            # 创建参数占位符
            param_name = f"x{self.param_counter}"
            self.param_counter += 1

            # 替换字段 - 保留原始格式
            orig_value = fields[field_idx]
            new_fields = []
            for i, field in enumerate(fields):
                if i == field_idx:
                    new_fields.append(f"${{{param_name}}}")
                else:
                    new_fields.append(field)

            # 重建行，保留原始逗号格式
            new_line = ",".join(new_fields)

            # 如果原行末尾有逗号，保留逗号
            if line.endswith(','):
                new_line += ','

            # 添加换行符
            new_line += '\n'
            self.lines[line_idx] = new_line

            self.param_map[param_name] = {
                "line": line_idx + 1,
                "field": field_idx + 1,
                "original_value": orig_value
            }

            print(f"✅ 已参数化: 行 {line_num} 字段 {field_num} ({orig_value} → ${{{param_name}}})")
            print(f"     | 新行内容: {new_line.strip()}")
            return True
        except Exception as e:
            print(f"❌ 参数化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def save_template(self):
        """保存模板文件"""
        try:
            with open(self.template_path, 'w', encoding='utf-8') as f:
                f.writelines(self.lines)
            print(f"💾 模板已保存: {self.template_path}")

            # 生成边界配置建议
            bounds = []
            for param, info in self.param_map.items():
                try:
                    orig_val = float(info['original_value'])
                    low_bound = max(0.1 * orig_val, orig_val * 0.5)
                    high_bound = min(10 * orig_val, orig_val * 2.0)
                    bounds.append((low_bound, high_bound))
                except ValueError:
                    print(f"⚠️ 无法转换原始值为浮点数: {info['original_value']}")

            print("\n建议的边界配置 (config.py 中更新 BOUNDS):")
            print(f"BOUNDS = {bounds}")
            return bounds
        except Exception as e:
            print(f"❌ 保存模板失败: {str(e)}")
            return []

    def interactive_edit(self):
        """交互式编辑流程"""
        print("\n" + "=" * 80)
        print("INP文件交互式参数化工具")
        print("=" * 80)

        self.load_file()

        # 显示文件开头
        self.display_lines(0, 20)

        while True:
            print("\n选项:")
            print("1. 显示更多内容")
            print("2. 参数化字段")
            print("3. 完成并保存模板")
            print("4. 退出")

            choice = input("请选择操作: ").strip()

            if choice == '1':
                start_line = input("输入起始行号 (默认为0): ").strip() or "0"
                try:
                    start = max(0, int(start_line) - 1)
                    self.display_lines(start, start + 20)
                except ValueError:
                    print("❌ 请输入有效数字")

            elif choice == '2':
                line_num = input("输入要参数化的行号: ").strip()
                field_num = input("输入要参数化的字段序号: ").strip()
                self.parameterize(line_num, field_num)

            elif choice == '3':
                if not self.param_map:
                    print("⚠️ 警告: 尚未添加任何参数")
                    confirm = input("确定要保存空模板吗? (y/n): ").lower()
                    if confirm != 'y':
                        continue

                return self.save_template()

            elif choice == '4':
                confirm = input("放弃所有更改并退出? (y/n): ").lower()
                if confirm == 'y':
                    print("退出编辑")
                    return []

            else:
                print("❌ 无效选择")