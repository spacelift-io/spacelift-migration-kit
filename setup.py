from setuptools import setup

setup(
    name="spacemk",
    version="0.1.0",
    packages=["spacemk"],
    entry_points={"console_scripts": ["spacemk = spacemk.__main__:cli"]},
)
