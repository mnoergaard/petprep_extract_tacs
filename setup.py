from setuptools import setup, find_packages

setup(
    name="petprep_extract_tacs",
    version="0.0.3",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "petprep_extract_tacs=petprep_extract_tacs.run:main",
        ],
    },
    url="https://github.com/mnoergaard/petprep_extract_tacs",
    author="Martin Norgaard",
    author_email="martin.noergaard@di.ku.dk",
    description="PETPrep Extraction of Time Activity Curves",
)
