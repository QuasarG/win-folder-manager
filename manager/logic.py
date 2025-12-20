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
        if os.name != 'nt':
            return

        if os.path.exists(ini_path):
            subprocess.run(['attrib', '+s', '+h', ini_path], shell=True)

        subprocess.run(['attrib', '-r', folder_path], shell=True)
        subprocess.run(['attrib', '+r', folder_path], shell=True)

    def remove_attributes_before_write(self, ini_path):
        """写入前必须移除系统和隐藏属性，否则无法写入"""
        if os.name != 'nt':
            return

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
            try:
                with open(ini_path, 'r', encoding='utf-16') as f:
                    content = f.read()
            except:
                try:
                    with open(ini_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except:
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
                    try:
                        icon_raw_part = line.split("=", 1)[1].strip()
                        raw_path = icon_raw_part.split(",")[0].strip()

                        if not raw_path:
                            continue

                        if not os.path.isabs(raw_path):
                            abs_path = os.path.join(folder_path, raw_path)
                        else:
                            abs_path = raw_path

                        final_path = os.path.normpath(os.path.abspath(abs_path))

                        info["icon_path"] = final_path
                    except Exception as icon_err:
                        print(f"Icon parse error: {icon_err}")

        except Exception as e:
            print(f"Error reading {ini_path}: {e}")

        return info

    def update_folder(self, folder_path, alias, icon_path, infotip, use_relative=False):
        ini_path = self.get_ini_path(folder_path)

        final_icon_path = icon_path
        if use_relative and icon_path and os.path.exists(icon_path):
            try:
                rel = os.path.relpath(icon_path, folder_path)
                final_icon_path = rel
            except ValueError:
                pass

        lines = ["[channel]", "[.ShellClassInfo]"]

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

        self.remove_attributes_before_write(ini_path)

        with open(ini_path, 'w', encoding='utf-16') as f:
            f.write(content)

        self.set_attributes(folder_path, ini_path)
        return True

    def scan_folders(self, root_path):
        if not os.path.exists(root_path):
            return []

        result = []
        try:
            with os.scandir(root_path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        result.append(self.read_folder_info(entry.path))
        except Exception as e:
            print(f"Scan error: {e}")

        return result
