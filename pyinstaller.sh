#wget https://files.pythonhosted.org/packages/83/4a/7b9eca3c9ded03a285a0044f3fb18d85e80819da62249888ecfac5a5df46/pyinstaller-4.9-py3-none-manylinux2014_x86_64.whl
#pip3 install pyinstaller-4.9-py3-none-manylinux2014_x86_64.whl
pyinstaller \
  --paths `pwd`/src/lib \
  --paths `pwd`/src/Workflow/ \
  --add-data src/config:config \
  --ascii --clean \
  -F \
  src/pipeline_generate.py
rm -rf build
# 修改pipeline_generate.spec，将datas中加入config，打包配置文件
#pyinstaller pipeline_generate.spec
#cd `pwd` && ln -snf dist/pipeline_generate STPG

