from setuptools import setup, find_packages

setup(
    name='petprep_extract_tacs',
    version='0.0.1',
    packages=find_packages(),
    package_dir={"": "petprep_extract_tacs"},
    url='https://github.com/mnoergaard/petprep_extract_tacs',
    author='Martin Norgaard',
    author_email='martin.noergaard@di.ku.dk',
    description='PETPrep Extraction of Time Activity Curves'
)