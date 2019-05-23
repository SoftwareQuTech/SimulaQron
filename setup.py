import setuptools
import os

path_to_here = os.path.dirname(os.path.abspath(__file__))
simulaqron_init = os.path.join(path_to_here, "simulaqron", "__init__.py")

with open(simulaqron_init, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith("__version__"):
            version = line.split("__version__ = ")[1]
            version = version.split(' ')[0]
            version = eval(version)
            break
    else:
        raise RuntimeError("Could not find the version!")

with open("README.md", 'r') as f:
    long_description = f.read()

with open("requirements.txt", 'r') as f:
    install_requires = [line.strip() for line in f.readlines()]

setuptools.setup(
    name="simulaqron",
    version=version,
    author="Axel Dahlberg",
    author_email="e.a.dahlberg@tudelft.nl",
    description="A simulator for developing Quantum Internet software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SoftwareQuTech/SimulaQron",
    include_package_data=True,
    packages=setuptools.find_packages(include=("simulaqron*",)),
    package_data={
        'simulaqron': ['config/.keep', '.simulaqron_pids/.keep', 'tests/unittests/slow/merges/configs/*.cfg']
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
