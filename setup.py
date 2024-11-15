from setuptools import setup

setup(
    name='dvc-utils',
    version="0.1.0",
    description="CLI for diffing DVC files at two commits (or one commit vs. current worktree), optionally passing both through another command first",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=['dvc_utils'],
    install_requires=open("requirements.txt").read(),
    entry_points={
        'console_scripts': [
            'dvc-utils = dvc_utils.cli:cli',
            'dvc-diff = dvc_utils.cli:dvc_utils_diff',
        ],
    },
    license="MIT",
    author="Ryan Williams",
    author_email="ryan@runsascoded.com",
    author_url="https://github.com/ryan-williams",
    url="https://github.com/runsascoded/dvc-utils",
)
