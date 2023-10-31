from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="rekdoc",  
    # packages=find_packages(where="."), 
    include_package_data=True,
    packages=find_packages(), 
    version="1.0.0",  
    description="A document generation program",  
    long_description='A document is generated by using a asserted data from ILOM and Explorer files of a Oracle Solaris or Linux machine.',
    long_description_content_type="text/plain", 
    author="Rek3000", 
    author_email="torek3k@example.com",
    python_requires=">=3",
    install_requires=["python-docx", 'wand', 'click'], 
    extras_require={
        "dev": ["pex"],
    },
    entry_points={
        'console_scripts': [
            'rekdoc = rekdoc.core:cli',
            ],
        }
)
