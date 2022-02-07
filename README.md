# Standard template pipeline generater(STPG) 

## STPG ���
STPG ��һ������ģ��Ԥ����ķ�ʽ�����ض��������̵��Զ������ߣ�����makefile��yaml�ȼ�������ʵ�֣���Ҫ����Ϊһ���µ��������˼·����ϸ��Ϣ��[�Ķ���չ����](https://zhuanlan.zhihu.com/p/449187702) ��  
�����������̶����в��ýű�����װ�ķ�ʽ�����������̵���չ������������Եȣ�ͨ���淶����ģ�������������̣��ǳ����ģ��Ⱥ�����ݷ����ı�Ҫ���ߡ�
## STPG ʹ�÷���
### 2.1 һ��ʾ��
```shell
STPG \
  -b $(pipeline-bin) \
  -c $(job-root)/config.ini \
  -pro $(job-name) \
  -t $(pipeline-bin)/Config/pipeline.yaml \
  -m sge-singularity-sjm \
  -o $(job-root) \
  -tc $(pipeline-bin)/Script/piplinetool.config \
  -r
```
### 2.2 ��������
* -b/--bin  
ָ��Ϊ�ض����̵ĸ�Ŀ¼����Ŀ¼�´���Modules�ļ��У�Modules�ļ����ڴ洢����ģ���makefile�ļ�����-t����ָ���ļ����е��ã�  
* -c/--config
�������޹ض����ض�����Ŀ�йص������ļ�����д���������̵��ã��ο��������£�
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
������Ŀ������
* -t/--template 
�����������е�ģ���ļ�����¼ģ����������������Դ�������Լ�ģ������ȣ�ʾ�����£�
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
* -m/--method  
����ļܹ������Լ���ԴͶ���������ͣ�Ŀǰ֧�����£�
  * sge-singularity-sjm 
  * sge-docker-sjm
  * sge-normal-sjm  
��������Ϊ��
  * sge-docker-wdl
  * k8s-docker-argo

* -o/--outdir  
�������̵����Ŀ¼
* -tc/--toolconfig
�������е������ļ���Ĭ��ʹ��`config/tool_config.ini`�ļ���
* -r/--run����ѡ��
����ѡ��ָ��ʱ�������̺�ֱ��Ͷ����������
* -p/--point 
����������ʼ�㣬���������ģ���е�����һ����ģ�����ģ�飬��ʼ����ǰ������ģ���ǿ�ж���Ϊ��ɡ�  
* -l/--list����ѡ��
ѡ��ģ���е�һ������ģ����з���������ָ�����б��ļ���Ϊһ��
    ```text
    taskA
    taskB
    ```  
## STPG ��������̹淶
һ�����̲������½ṹ
```text
|-- Config  # �����ļ�Ŀ¼
|   |-- config_mk.ini   # makefileʹ�õ������ļ��������config_software���������ڡ�[]��ǰ���ϡ�#��
|   |-- config_software # ����perl��python�ű����������ļ�
|   |-- create_mkini.sh # config_softwareתconfig_mk.ini�Ľű�
|   |-- pipeline.yaml   # ����ģ���ļ���-t������
|   |-- job.list        # ��������ģ���б��ļ���-l������
|-- Modules
|   |-- test.mk         # ����������ļ�
|-- README.md           # ����˵���ļ�
|-- Readme              # ���˵�����ļ���
|   |-- 0.readme.txt
|-- Script              # �����Ĺ��ܽű�
|   |-- Basic
|   `-- piplinetool.config  # ������صĹ��������ļ���-tc������
`-- report
    |-- �����ļ�
```
## STPG ��չ
### Cromwell-WDL
### K8S-ARGO