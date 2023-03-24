# from Workflow.K8S_argo.argo_workflow import ARGO_workflow
# from Workflow.K8s_Argo_Hera.argo_hera_dag import ArgoHera_Job
from Workflow.BaseParserJob.baseworkflow import Parser_Job
### workflow method import  ###
from Workflow.Cromwell.WDL_workflow import WDL_Workflow
from Workflow.K8S_Argo_couler.argo_couler_workflow import ArgoCouler
from Workflow.SGE_SJM.SJM_DAG import SJM_Job
from Workflow.BaseParserJob.baseworkflow import GlobalPara

method2class = {SJM_Job.Name:SJM_Job,
                WDL_Workflow.Name:WDL_Workflow,
                # ArgoHera_Job.Name:ArgoHera_Job,
                ArgoCouler.Name:ArgoCouler,
                Parser_Job.Name:Parser_Job}

