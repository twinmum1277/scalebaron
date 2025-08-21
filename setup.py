from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='scalebaron',
    version='1.0.0',
    description='ScaleBarOn: A Python Tool for Scaling Multiple Elemental Maps',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tracy Punshon',
    author_email='tracy.punshon@dartmouth.edu',
    license='MIT',
    packages=['scalebaron'],
    install_requires=requirements,
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
