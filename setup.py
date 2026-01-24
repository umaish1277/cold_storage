from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="cold_storage",
    version="0.1.0",
    description="Cold Storage operations + billing for ERPNext",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
