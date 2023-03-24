# import sys,os
# sys.path.append('../../src')
import base64
import errno
from typing import Callable, Dict, List, Optional, Union

from Workflow.BaseParserJob.baseworkflow import Parser_Job, JOB_attribute
from hera import (
    EnvSpec,
    ExistingVolume,
    InputFrom,
    Resources,
    Retry,
    Task,
    Toleration,
    OutputPathParameter,
    InputParameter,
    Workflow,
    WorkflowService,
    TaskSecurityContext,
    workflow_status
)
from kubernetes import config, client
from lib.public_method import *
# argo hera
from pydantic import BaseModel


# from lib.graph import DFSVertext


def generate_token() -> str:
    """Abstractly, generates a client Bearer token that passes auth with the Argo server for workflow submission"""
    return 'my-bearer-token'

def get_sa_token(service_account: str, namespace: str , config_file: Optional[str] = None):
    """Get ServiceAccount token using kubernetes config.

     Parameters
    ----------
    service_account: str
        The service account to authenticate from.
    namespace: str = 'default'
        The K8S namespace the workflow service submits workflows to. This defaults to the `default` namespace.
    config_file: Optional[str] = None
        The path to k8s configuration file.

     Raises
    ------
    FileNotFoundError
        When the config_file can not be found.
    """
    if config_file is not None and not os.path.isfile(config_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_file)

    config.load_kube_config(config_file=config_file)
    v1 = client.CoreV1Api()
    secret_name = v1.read_namespaced_service_account(service_account, namespace).secrets[0].name
    sec = v1.read_namespaced_secret(secret_name, namespace).data
    return base64.b64decode(sec["token"]).decode()

class MyWorkflowService(WorkflowService):
    """Internal WorkflowService wrapper around Hera's WorkflowService to support consistency in auth token generation"""

    def __init__(self, host: str = 'https://my-argo-domain.com', namespace="argo", token: str = get_sa_token("argo-server","argo")):
        super(MyWorkflowService, self).__init__(host=host, token=token, namespace='my-default-k8s-namespace')


class MyWorkflow(Workflow):
    """Internal Workflow wrapper around Hera's Workflow to support consistent MyWorkflowService usage"""

    def __init__(self, name: str, service: WorkflowService = MyWorkflowService(host="https://10.0.8.10:30123/",namespace="argo"), parallelism: int = 50):
        super(MyWorkflow, self).__init__(name, service, parallelism=parallelism)

class MyTaskSecurityContext(TaskSecurityContext):
    def __init__(self):
        run_as_user = 5000
        run_as_group = 511
        run_as_non_root = True
        super(MyTaskSecurityContext).__init__()

def execute_cmd_inline(cmd):
    os.system(cmd)

class MyTask(Task):
    """Internal Task wrapper around Hera's Task to set usage defaults"""

    def __init__(
        self,
        name: str,
        func: Callable,
        func_params: Optional[List[Dict[str, Union[int, str, float, dict, BaseModel]]]] = None,
        input_from: Optional[InputFrom] = None,
        image: str = 'python:3.7',
        command: Optional[List[str]] = None,
        env_specs: Optional[List[EnvSpec]] = None,
        resources: Resources = Resources(),
        tolerations: Optional[List[Toleration]] = None,
        taskOne: JOB_attribute = None,
        working_dir: str = '/my-volume'
    ):
        default_retry = Retry(duration=1, max_duration=20)
        self.taskOne = taskOne
        self.inputs = []
        self.outputs = []
        self.security_context = MyTaskSecurityContext
        # note that this gke-accelerator spec is only valid for GKE GPUs. For Azure and AWS you
        # might have to use the `node_selectors` field exclusively
        default_node_selectors = {}#{'cloud.google.com/gke-accelerator': 'nvidia-tesla-k80'}
        super(MyTask, self).__init__(
            name,
            func,
            func_params,
            input_from=input_from,
            image=image,
            command=command,
            env_specs=env_specs,
            resources=resources,
            working_dir=working_dir,
            retry=default_retry,
            tolerations=tolerations,
            node_selectors=default_node_selectors,
            inputs=self.inputs,
            outputs=self.outputs
        )
        self.parameter_loading()
    def volumes_define(self, mount_list):
        volumes = []
        for idx, mount in enumerate(mount_list):
            OutsideContainerDir = mount.strip().split(":")[0]
            volumes.append(ExistingVolume(mount_path=OutsideContainerDir, name=f"mount-{idx}"))
        self.resources.volumes.extend(volumes)

    def InputAndOutput(self,inputlist, outputobject):
        self.inputs = [ InputParameter('input_'+str(idx),'',infile) for idx,infile in enumerate(inputlist) ]
        self.outputs = [ OutputPathParameter(key, value) for key, value in outputobject.__dict__ if not key.startswitch('__') ]

    def parameter_loading(self):
        self.volumes_define(self.taskOne.Mount)
        self.InputAndOutput(self.taskOne.Input, self.taskOne.Output)

        if not self.taskOne.CPU:     self.resources.max_cpu = self.taskOne.CPU
        if not self.taskOne.Memory:  self.resources.max_mem = self.taskOne.Memory
        if not self.taskOne.Image:   self.image = self.taskOne.Image
        if not self.taskOne.Command: self.command = ['sh', '-c', self.taskOne.Command]

class ArgoHera_Job(Parser_Job):
    Name = "k8s-argo-Hera"
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project):
        self.job_file = job_file
        self.separate = ";"
        self.para = parameter
        self.mount_list = []
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.project = project
        self.outdir = outdir
        self.sjm_method = sjm_method
        self.workflow = MyWorkflow(f'workflow-{project}')
        super(ArgoHera_Job,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)

    def write_jobs_to_DAG(self, ):
        all_task_list = self.pipelineGraph.getVertices()
        already_addjobs = {}
        for one_a_job in all_task_list:
            onemytask = MyTask(taskOne=one_a_job,name=one_a_job.Name,func=execute_cmd_inline, working_dir=self.outdir)
            # self.pipelineGraph.getVertex(one_a_job).id = onemytask
            already_addjobs[one_a_job.Name] = onemytask
            self.workflow.add_task(onemytask)
            # for one_depend in self.pipelineGraph.getVertex(one_a_job).prefix:
            #     if one_depend.Name in already_addjobs:
            #         already_addjobs[one_depend.id.Name].next(onemytask)
        for one_a_job in all_task_list:
            for depend_job in self.pipelineGraph.getVertex(one_a_job).getConnections():
                already_addjobs[one_a_job.Name].next(already_addjobs[depend_job.Name])

    def define_sjm_one_job(self, one_job, ):
        pass

    def write_Command_to_file(self):
        """
        重载command，argo-hera模式下不生成shell，但是会将换行+&&更改为";"
        """
        # allTaskObject = self.pipelineGraph.getVertices()
        # for taskObject in allTaskObject:
        #     taskObject.id.Command = []
        pass

    def create_other_shsh(self):
        pass

    def delivary_pipeline(self, is_run=True, log_file='', guard=True):
        if is_run:
            create_back = self.workflow.create()
            print(create_back)
            if guard:
                while self.workflow.service.get_workflow_status() == workflow_status.WorkflowStatus.Running:
                    pass
