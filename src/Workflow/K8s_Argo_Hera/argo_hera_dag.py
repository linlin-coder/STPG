from lib.public_method import *
from pipeline_generate import Parser_Job
from Workflow.version import tool_bin as bin_tool

# argo hera
from typing import Callable, Dict, List, Optional, Union
from pydantic import BaseModel
from hera import (
    EnvSpec,
    ExistingVolume,
    InputFrom,
    Resources,
    Retry,
    Task,
    Toleration,
    Workflow,
    WorkflowService,
)


def generate_token() -> str:
    """Abstractly, generates a client Bearer token that passes auth with the Argo server for workflow submission"""
    return 'my-bearer-token'


class MyWorkflowService(WorkflowService):
    """Internal WorkflowService wrapper around Hera's WorkflowService to support consistency in auth token generation"""

    def __init__(self, host: str = 'https://my-argo-domain.com', token: str = generate_token()):
        super(MyWorkflowService, self).__init__(host=host, token=token, namespace='my-default-k8s-namespace')


class MyWorkflow(Workflow):
    """Internal Workflow wrapper around Hera's Workflow to support consistent MyWorkflowService usage"""

    def __init__(self, name: str, service: WorkflowService = MyWorkflowService(), parallelism: int = 50):
        super(MyWorkflow, self).__init__(name, service, parallelism=parallelism)


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
    ):
        default_retry = Retry(duration=1, max_duration=20)
        # note that this gke-accelerator spec is only valid for GKE GPUs. For Azure and AWS you
        # might have to use the `node_selectors` field exclusively
        default_node_selectors = {'cloud.google.com/gke-accelerator': 'nvidia-tesla-k80'}
        default_working_dir = '/my-volume'
        resources.existing_volume = ExistingVolume(name='my-volume', mount_path='/my-volume')
        super(MyTask, self).__init__(
            name,
            func,
            func_params,
            input_from=input_from,
            image=image,
            command=command,
            env_specs=env_specs,
            resources=resources,
            working_dir=default_working_dir,
            retry=default_retry,
            tolerations=tolerations,
            node_selectors=default_node_selectors,
        )

class ArgoHera_Job(Parser_Job,Deliver_DAG_Job):
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project):
        self.job_file = job_file
        # self.project_configdir = args.config
        self.para = parameter
        self.mount_list = []
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.project = project
        self.outdir = outdir
        self.sjm_method = sjm_method
        self.workflow = MyWorkflow(f'workflow-{project}')
        super(SJM_Job,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)

    def write_jobs_to_DAG(self, ):
        all_task_list = self.pipelineGraph.getVertices()
        for one_a_job in all_task_list:


    def define_sjm_one_job(self, one_job, ):
        pass

    def write_Command_to_file(self):
        pass

    def create_other_shsh(self):
        pass

    def delivary_pipeline(self, is_run=True, log_file='', guard=True):
        pass
