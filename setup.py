from setuptools import setup
from pathlib import Path

this_dir = Path(__file__).parent


def read_requirements(filename):
    path = this_dir / filename
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


core_requirements = read_requirements("requirements.txt")
optional_requirements = read_requirements("requirements-optional.txt")

long_description = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name='scalebaron',
    version='1.0.2',
    description='ScaleBarOn: A Python Tool for Scaling Multiple Elemental Maps',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tracy Punshon',
    author_email='tracy.punshon@dartmouth.edu',
    license='MIT',
    packages=['scalebaron'],
    package_data={'scalebaron': ['icons/*.png', 'icons/*.svg']},
    install_requires=core_requirements,
    extras_require={
        'optional': optional_requirements,
        'full': optional_requirements,
    },
    entry_points={
        'console_scripts': [
            'scalebaron = scalebaron.scalebaron:main',
            'muaddata = scalebaron.muaddata:main',
            'download_test_elemental_images = scalebaron.download:main'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
