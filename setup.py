from setuptools import setup, find_packages

long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="aquastilla_softener",
    description="Library to fetch data from Aquastilla softener from Viessmann API",
    long_description=long_description,
    version="0.1.5",
    license="GPL",
    author="Tomasz Szymanowicz",
    author_email="alakdae@gmail.com",
    packages=find_packages(),
    url="https://github.com/alakdae/aquastilla-softener",
    keywords="aquastilla softener aquastilla_softener",
)
