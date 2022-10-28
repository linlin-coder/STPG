# Standard template pipeline generater(STPG) 

## STPG 简介
STPG 是一个基于模板预定义的方式生成特定分析流程的自动化工具，基于makefile、yaml等技术进行实现，主要表现为一种新的流程设计思路，详细信息请[阅读扩展链接](https://zhuanlan.zhihu.com/p/449187702) 。  
在以往的流程定义中采用脚本逐层封装的方式，不利于流程的扩展迭代，报错调试等，通过规范流程模板批量生成流程，是超大规模集群中数据分析的必要工具。
## STPG 使用方法
### 2.1 一般示例
```shell
STPG \
  -b $(pipeline-bin) \
  -c $(job-root)/config.ini \
  -pro $(job-name) \
  -t $(pipeline-bin)/Config/pipeline.yaml \
  -m sge-singularity-sjm \
  -o $(job-root) \
  -tc $(pipeline-bin)/Script/piplinetool.config \
  -p $(pointname) \
  -r
```
### 2.2 参数介绍
* -b/--bin  
指定为特定流程的根目录，此目录下存在Modules文件夹（Modules文件夹内存储所有模块的makefile文件，被-t参数指定文件进行调用）  
* -c/--config  
与流程无关而和特定的项目有关的配置文件，填写参数被流程调用，参考内容如下：
    ```editorconfig
    [Sample]
    A1=B2-S	B2-S.R2
    B1=B1-S	B1-S
    C1=S	S.R2
    
    [Group]
    A1=A
    B1=B
    C1=C
    
    [Compare]
    AvsB=2	0.05	0.05
    
    [DB]
    DB_test=test
    
    [Para]
    Para_test=test
    ```  
* -pro/--project  
运行项目的名称
* -t/--template   
定义流程运行的模板文件，记录模块间的依赖、运行资源、镜像以及模块归属等,示例如下：
    ```yaml
    default:
        Queue: "test.q"
        Shell_dir: "{OUTDIR}/shell"
        CPU: 1
        Memory: "1G"
        Image: "alpine:3.13.5"
    
    pipeline:
        QC:
            merge_data:
    #            Shell_dir: "{OUTDIR}/Fastqc"
                Part: "Sample"
                Queue: "test.q"
                Image: "alpine:3.13.5"
                Depend:
                    -
                Command: "{make} -f {BIN}/Modules/QC.mk  outdir={OUTDIR} sample_id={Part[0]} merge_data"
            qc:
    #            Shell_dir: "{OUTDIR}/Fastqc"
                Depend:
                    - "merge_data_{Part[0]}"
                Part: "Sample"
                Command:
                    - "{make} -f {BIN}/Modules/QC.mk sample_id={Part[0]} outdir={OUTDIR} qc"
                    - "echo yes && whoami"
            qc_summary:
    #            Shell_dir: "{OUTDIR}/Fastqc"
                Image: "alpine:3.13.5"
                Depend:
                    - "qc"
                    - "merge_data"
                Command: "{make} -f {BIN}/Modules/QC.mk outdir={OUTDIR} scriptdir={OUTDIR} qc_summary"
    ```    
迭代区数据如何使用：  
    `Part`指定对`config.ini`文件那个区域进行迭代，此区域的信息格式最好一致，`TAB`键分隔；`Part[0]`指的是`=`左边的值，`Part[1]`到`Part[n]`指的是`=`右边并在按`TAB`键分隔后的值
数据库参数的引用：  
指定在在`config.ini`文件中`DB`区域以`DB_`开头的参数，例如`DB_test`。  
其他参数的引用：  
指定在在`config.ini`文件中`Para`区域以`Para_`开头的参数，例如`Para_test`。  
如何定义模块和模块间的依赖关系，所有的依赖情况为：
  1. 依赖主模块里的所有子模块；  
  ```text
  Depend:
    - "QC"
  ```    
  2. 依赖主模块里的单个子模块；  
  ```text
  Depend:
    - "qc_summary"
  ```    
  3. 依赖主模块中有迭代区的单个子模块。  
  ```text
  Depend:
    - "merge_data_{Part[0]}"
  ```    
* -m/--method    
超算的架构类型以及资源投递器的类型，目前支持如下：
  * sge-singularity-sjm 
  * sge-docker-sjm
  * sge-normal-sjm  
待开发的为：
  * sge-docker-wdl
  * k8s-docker-argo

* -o/--outdir    
生成流程的输出目录
* -tc/--toolconfig  
工具运行的配置文件，默认使用`config/tool_config.ini`文件。
* -r/--run（可选）  
布尔选择，指定时生成流程后直接投递任务流。
* -p/--point   
流程运行起始点，这里可以是模板中的任意一个主模块或子模块，起始点以前的所有模块均强行定义为完成。  
* -l/--list（可选）  
选择模板中的一部分主模块进行分析，进行指定的列表文件，为一个yaml文件
    ```text
    # 分析一个主模块下部分子模块
    QC：
     - "qc"
     - "merge_data"
    # 分析主模块的所有内容
    QC：
    # 不分析该主模块
    yaml文件中不填写即可
    ```  
### 2.3 软件重新打包
参考`pyinstaller.sh`文件中的代码，主要使用pyinstaller工具进行打包，核心代码如下：
```shell
pyinstaller \
  --paths `pwd`/src/lib \
  --paths `pwd`/src/Workflow/ \
  --add-data src/config:config \
  --ascii --clean \
  -F \
  src/pipeline_generate.py
```
## STPG 适配的流程规范
一般流程采用如下结构
```text
|-- Config  # 配置文件目录
|   |-- config_mk.ini   # makefile使用的配置文件，相较于config_software差异在于在“[]”前加上“#”
|   |-- config_software # 部分perl、python脚本所用配置文件
|   |-- create_mkini.sh # config_software转config_mk.ini的脚本
|   |-- pipeline.yaml   # 流程模板文件（-t参数）
|   |-- job.list.yaml   # 待分析的模块列表文件（-l参数）
|-- Modules
|   |-- test.mk         # 定义命令的文件
|-- README.md           # 流程说明文件
|-- Readme              # 结果说明的文件夹
|   |-- 0.readme.txt
|-- Script              # 分析的功能脚本
|   |-- Basic
|   `-- piplinetool.config  # 流程相关的工具配置文件（-tc参数）
`-- report
    |-- 报告文件
```
## STPG 扩展
### Cromwell-WDL
### K8S-ARGO