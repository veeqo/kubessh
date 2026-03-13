import setuptools

setuptools.setup(
    name="kubessh",
    version='0.1',
    url="https://github.com/yuvipanda/kubessh",
    author="Yuvi Panda",
    author_email="yuvipanda@gmail.com",
    license="Apache-2",
    description="SSH server to spawn users into kubernetes pods",
    packages=setuptools.find_packages(),
    install_requires=[
        'kubernetes==31.0.0',
        'asyncssh==2.21.1',
        'ptyprocess==0.7.0',
        'aiohttp==3.11.18',
        'traitlets==5.14.3',
        'escapism==1.0.1',
        'ruamel.yaml==0.18.10',
        'simpervisor==1.0.0'
    ],
    entry_points = {
        'console_scripts': [
            'kubessh=kubessh.app:main'
        ]
    }
)