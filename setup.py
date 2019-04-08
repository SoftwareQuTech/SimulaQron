import setuptools


with open("README.md", 'r') as f:
    long_description = f.read()

with open("requirements.txt", 'r') as f:
    install_requires = [line.strip() for line in f.readlines()]

setuptools.setup(
    name="simulaqron",
    version="2.2.0",
    author="Axel Dahlberg",
    author_email="e.a.dahlberg@tudelft.nl",
    description="A simulator for developing Quantum Internet software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SoftwareQuTech/SimulaQron",
    include_package_data=True,
    packages=setuptools.find_packages(include=("simulaqron*",)),
    package_data={
        'simulaqron': ['config/*.cfg', '.simulaqron_pids/__keep__', 'tests/auto/quick/merges/configs/*.cfg']
    },
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: MacOS"
    ],
    entry_points='''
        [console_scripts]
        simulaqron=simulaqron.SimulaQron:cli
    '''
)
