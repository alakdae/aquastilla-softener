from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="aquastilla_softener",
    description="Library to fetch data from Aquastilla softener from Viessmann API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.1.8",
    license="GPL",
    author="Tomasz Szymanowicz",
    author_email="alakdae@gmail.com",
    packages=find_packages(),
    url="https://github.com/alakdae/aquastilla-softener",
    keywords="aquastilla softener aquastilla_softener",
)
