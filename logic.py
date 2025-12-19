import os
import subprocess
import configparser
import io


class FolderManager:
    def __init__(self, config_path):
        self.config_path = config_path

    def get_ini_path(self, folder_path):
        return os.path.join(folder_path, "desktop.ini")

    def set_attributes(self, folder_path, ini_path):
        """
        核心操作：设置文件为系统+隐藏，文件夹为只读。
        这是Windows识别自定义图标的必要条件。
        """
        # 1. 设置 desktop.ini 为 系统文件(s) + 隐藏(h)
        if os.path.exists(ini_path):
            subprocess.run(['attrib', '+s', '+h', ini_path], shell=True)

        # 2. 设置文件夹为 只读(r) (这不会导致文件不可写，只是一个Flag)
        # 先移除再添加，强制刷新缓存
        subprocess.run(['attrib', '-r', folder_path], shell=True)
        subprocess.run(['attrib', '+r', folder_path], shell=True)

    def remove_attributes_before_write(self, ini_path):
        """写入前必须移除系统和隐藏属性，否则无法写入"""
        if os.path.exists(ini_path):
            subprocess.run(['attrib', '-s', '-h', ini_path], shell=True)

    def read_folder_info(self, folder_path):
        ini_path = self.get_ini_path(folder_path)
        info = {
            "path": folder_path,
            "name": os.path.basename(folder_path),
            "alias": "",
            "icon_path": "",
            "infotip": "",
            "has_ini": False
        }

        if not os.path.exists(ini_path):
            return info

        info["has_ini"] = True
        try:
            content = ""
            # 尝试多种编码读取
            try:
                with open(ini_path, 'r', encoding='utf-16') as f:
                    content = f.read()
            except:
                try:
                    with open(ini_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except:
                    # 最后尝试 utf-8，防止有人手动改成了 utf-8
                    with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.lower().startswith("localizedresourcename="):
                    info["alias"] = line.split("=", 1)[1].strip()

                if line.lower().startswith("infotip="):
                    info["infotip"] = line.split("=", 1)[1].strip()

                if line.lower().startswith("iconresource="):
                    # 获取原始路径，例如: ..\_resource\BxTask.ico,0
                    try:
                        icon_raw_part = line.split("=", 1)[1].strip()
                        # 去掉可能存在的 ,0 或 ,-1 索引
                        raw_path = icon_raw_part.split(",")[0].strip()

                        # === 核心：绝对路径计算与标准化 ===
                        if not raw_path:
                            continue

                        # 如果是相对路径，转换为绝对路径
                        if not os.path.isabs(raw_path):
                            abs_path = os.path.join(folder_path, raw_path)
                        else:
                            abs_path = raw_path

                        # normpath 会解决 "D:/Project/../icon.ico" 这种中间带点的路径，也会统一分隔符为 \
                        final_path = os.path.normpath(
                            os.path.abspath(abs_path))

                        info["icon_path"] = final_path
                    except Exception as icon_err:
                        print(f"Icon parse error: {icon_err}")

        except Exception as e:
            print(f"Error reading {ini_path}: {e}")

        return info

    def update_folder(self, folder_path, alias, icon_path, infotip, use_relative=False):
        ini_path = self.get_ini_path(folder_path)

        # 处理路径转换
        final_icon_path = icon_path
        if use_relative and icon_path and os.path.exists(icon_path):
            try:
                # 计算相对路径
                rel = os.path.relpath(icon_path, folder_path)
                final_icon_path = rel
            except ValueError:
                # 跨盘符无法计算相对路径
                pass

        # 准备内容
        lines = ["[channel]", "[.ShellClassInfo]"]  # [channel] 有助于某些win版本识别

        if final_icon_path:
            lines.append(f"IconResource={final_icon_path},0")

        if alias:
            lines.append(f"LocalizedResourceName={alias}")

        if infotip:
            lines.append(f"InfoTip={infotip}")

        lines.append("[ViewState]")
        lines.append("Mode=")
        lines.append("Vid=")
        lines.append("FolderType=Generic")

        content = "\n".join(lines)

        # 写入流程
        self.remove_attributes_before_write(ini_path)

        # 强制使用 utf-16 写入 (带BOM)，这是最稳健的格式
        with open(ini_path, 'w', encoding='utf-16') as f:
            f.write(content)

        self.set_attributes(folder_path, ini_path)
        return True

    def scan_folders(self, root_path):
        if not os.path.exists(root_path):
            return []

        result = []
        try:
            # 只扫描一级目录
            with os.scandir(root_path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        result.append(self.read_folder_info(entry.path))
        except Exception as e:
            print(f"Scan error: {e}")

        return result
