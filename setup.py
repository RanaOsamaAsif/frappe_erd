from setuptools import find_packages, setup

with open("requirements.txt") as f:
	install_requires = [line for line in f.read().strip().split("\n") if line and not line.startswith("#")]

from frappe_erd import __version__ as version

setup(
	name="frappe-erd",
	version=version,
	description="A focused ERD Viewer app for Frappe",
	author="frappe-erd contributors",
	author_email="",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
