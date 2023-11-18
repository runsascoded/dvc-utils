from setuptools import setup

setup(
    name='dvc-utils',
    version="0.0.1",
    install_requires=open("requirements.txt").readlines(),
    packages=['dvc_utils'],
    entry_points={
        'console_scripts': [
            'dvc-utils = dvc_utils.main:cli',
        ],
    },
)
