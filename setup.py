# see https://packaging.python.org/tutorials/packaging-projects/#configuring-metadata

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    install_require = f.read().splitlines()

setuptools.setup(
    name="ada_client",
    version="0.0.4",
    author="NOIRLab Astro Data Archive",
    author_email="astroarchive@noirlab.edu",
    description= ("A client for getting metadata from "
                  "the NOIRLab Astro Data Archive."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NOAO/ada-client",
    project_urls={
        "NOIRLab Astro Data Archive": "https://astroarchive.noirlab.edu/",
    #!     "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    #! package_dir={"": "src"},
    packages=setuptools.find_packages(),
    install_requires=install_require,
    python_requires=">=3.6",
)
