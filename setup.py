import io
import os
import re
from setuptools import setup, find_packages


def read_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with io.open(os.path.join(here, 'manager', '__init__.py'), 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", content, re.M)
    if m:
        return m.group(1)
    return '0.0.0'


def read_requirements():
    req_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'requirements.txt')
    if not os.path.exists(req_file):
        return []
    with open(req_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


setup(
    name='win-folder-manager',
    version=read_version(),
    description='Windows desktop.ini folder manager web UI',
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires='>=3.8',
    entry_points={'console_scripts': ['win-folder-manager=manager.app:run']},
)
