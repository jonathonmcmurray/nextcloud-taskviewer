from setuptools import setup, find_packages

setup(
    name="nextcloud-task-backend",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "aiosqlite>=0.19.0",
        "caldav>=2.0.1",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.6",
    ],
    entry_points={
        "console_scripts": [
            "task-backend=src.main:main",
        ],
    },
)