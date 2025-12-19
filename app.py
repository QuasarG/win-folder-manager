import os
import json
import webbrowser
from threading import Timer
from flask import Flask, render_template, jsonify, request
from logic import FolderManager

app = Flask(__name__)

# 配置文件的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"root_path": "D:\\Project", "icons": []}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# 初始化逻辑类
folder_logic = FolderManager(CONFIG_FILE)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        new_config = request.json
        save_config(new_config)
        return jsonify({"status": "success"})
    return jsonify(load_config())


@app.route('/api/folders')
def get_folders():
    config = load_config()
    root = config.get('root_path', '')
    if not root:
        return jsonify([])
    folders = folder_logic.scan_folders(root)
    return jsonify(folders)


@app.route('/api/update', methods=['POST'])
def update_folder():
    data = request.json
    path = data.get('path')
    alias = data.get('alias')
    icon_path = data.get('icon_path')
    infotip = data.get('infotip')
    use_relative = data.get('use_relative', False)

    if not path:
        return jsonify({"status": "error", "msg": "No path provided"}), 400

    try:
        folder_logic.update_folder(
            path, alias, icon_path, infotip, use_relative)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route('/api/open', methods=['POST'])
def open_path():
    data = request.json
    path = data.get('path')
    mode = data.get('mode', 'explorer')  # explorer or cmd

    if not path or not os.path.exists(path):
        return jsonify({"status": "error", "msg": "Path not found"})

    if mode == 'cmd':
        os.system(f'start cmd /k "cd /d {path}"')
    else:
        os.startfile(path)

    return jsonify({"status": "success"})


@app.route('/api/batch_relative', methods=['POST'])
def batch_relative():
    """将所有文件夹的配置尝试转换为相对路径"""
    config = load_config()
    root = config.get('root_path', '')
    folders = folder_logic.scan_folders(root)

    count = 0
    for folder in folders:
        if folder['has_ini']:
            # 重新写入，开启 relative 开关
            folder_logic.update_folder(
                folder['path'],
                folder['alias'],
                folder['icon_path'],
                folder['infotip'],
                use_relative=True
            )
            count += 1
    return jsonify({"status": "success", "count": count})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:6800")


if __name__ == '__main__':
    # 启动后延时 1 秒打开浏览器
    Timer(1, open_browser).start()
    app.run(port=6800, debug=False)
