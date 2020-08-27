# coding=utf-8
import setuptools
import os

# 需要将那些包导入
packages = ["gevent_consumer",]


# 第三方依赖
requires = [
    "thrift==0.10.0",
    "thriftpy==0.3.9",
    "Django==1.9.10",
    "happybase==1.1.0",
    "gevent==1.2.2",
    "confluent-kafka==0.11.4",
]

about = {
    "__title__": "gevent consumer",
    "__version__": "1.0.0",
    "__description__": "A tool of base consumer",
    "__author__":"zy",
    "__author_email__":"zy362519070@outlook.com",
    "__url__":"www.notexist.com",
}


# 自动读取readme
with open('readme.md', 'r') as f:
    readme = f.read()

setuptools.setup(
    name=about["__title__"],  # 包名称
    version=about["__version__"],  # 包版本
    description=about["__description__"],  # 包详细描述
    long_description=readme,   # 长描述，通常是readme，打包到PiPy需要
    author=about["__author__"],  # 作者名称
    author_email=about["__author_email__"],  # 作者邮箱
    url=about["__url__"],   # 项目官网
    packages=packages,    # 项目需要的包
    data_files=None,   # 打包时需要打包的数据文件，如图片，配置文件等
    include_package_data=False,  # 是否需要导入静态数据文件
    python_requires=">=2.7.5, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3*",  # Python版本依赖
    install_requires=requires,  # 第三方库依赖
    zip_safe=False,  # 此项需要，否则卸载时报windows error
    classifiers=[    # 程序的所属分类列表
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
