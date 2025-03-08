from setuptools import setup, find_packages

setup(
    name="activity_logger",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["watchdog"],  # Add other dependencies here
    entry_points={"console_scripts": ["activity_logger=activity_logger.main:main"]},
)
