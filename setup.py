import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="line-tools",
    version="0.0.1",
    author="Douglas Liu",
    author_email="douglas@sohoffice.com",
    description="A small set of utility useful when creating line BOT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sohoffice/line-tools",
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': ['lt-rhythm=linetools.build_richmenu:main'],
    },
    install_requires=[
        'urllib3==1.23',
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
