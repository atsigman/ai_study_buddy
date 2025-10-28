from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()


setup(
    name="study_buddy_app",
    author="atsigman",
    packages=find_packages(),
    install_requires=requirements
)