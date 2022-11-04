#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：STPG 
@File ：argo_couler_workflow.py.py
@Author ：linlin
@Date ：2022/7/13 11:19 
'''
import os

import pyaml
from collections import OrderedDict
import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter
from couler.core.templates import (
    volume
)

from lib.public_method import *
from Workflow.BaseParserJob.baseworkflow import Parser_Job, JOB_attribute

couler.states.workflow.service_account = 'argo'

alreadymountdir: list = []

def add():
    num = 0
    while True:
        yield num
        num += 1

intNum = add()

def run_command(cmd):
    if os.system(cmd):
        std.info("running succese")
    else:
        std.warning("failed!!! run-cmd")

class Volume(volume.Volume):
    def __init__(self, name, path, type="Directory",):
        self.name = name
        self.path = path
        self.type = type
        super(Volume, self).__init__(name,name)

    def to_dict(self):
        return OrderedDict({
            "name": self.name,
            "hostPath": OrderedDict({
                "path": self.path,
                "type": self.type
            })
        })
class securityContext():
    @staticmethod
    def defineSecurityContext():
        return OrderedDict({
            "run_as_user": 5000,
            "run_as_group": 511,
            "run_as_non_root": True
        })
from hera.security_context import TaskSecurityContext

class MyTaskSecurityContext(TaskSecurityContext):
    def __init__(self):
        run_as_user = 5000
        run_as_group = 511
        run_as_non_root = True
        super(MyTaskSecurityContext).__init__()


class MyTask():
    """Internal Task wrapper around Hera's Task to set usage defaults"""

    def __init__(
        self,
        name: str,
        taskOne: JOB_attribute = None,
        working_dir: str = '/my-volume'
    ):
        self.taskOne = taskOne
        self.inputs = []
        self.outputs = []
        self.image = 'alpine:3.13.5'
        self.working_dir = working_dir
        # note that this gke-accelerator spec is only valid for GKE GPUs. For Azure and AWS you
        # might have to use the `node_selectors` field exclusively
        # default_node_selectors = {}#{'cloud.google.com/gke-accelerator': 'nvidia-tesla-k80'}
        self.parameter_loading()
    def volumes_define(self, mount_list):
        self.volumes = []
        for mount in mount_list:
            OutsideContainerDir = obtain_dir_rank(mount.strip().split(":")[0])
            if OutsideContainerDir and OutsideContainerDir in alreadymountdir:
                idx = alreadymountdir.index(OutsideContainerDir)
                self.volumes.append(volume.VolumeMount(mount_path=OutsideContainerDir, name=f"mount-{idx}"))
            if OutsideContainerDir and OutsideContainerDir not in alreadymountdir:
                alreadymountdir.append(OutsideContainerDir)
                idx = next(intNum)
                couler.add_volume(Volume(name=f"mount-{idx}",path=OutsideContainerDir))

    def InputAndOutput(self,inputlist, outputobject):
        return
        self.inputs = [ couler.create_parameter_artifact(path=infile) for idx,infile in enumerate(inputlist) ]
        self.outputs = [ couler.create_parameter_artifact(path=value) for key, value in outputobject.__dict__.items() if not key.startswith('__') if outputobject != None ]

    def parameter_loading(self):
        self.volumes_define(self.taskOne.Mount)
        self.InputAndOutput(self.taskOne.Input, self.taskOne.Output)

        self.TaskName = self.taskOne.Name
        if self.taskOne.CPU:     self.max_cpu = self.taskOne.CPU
        if self.taskOne.Memory:  self.max_mem = self.taskOne.Memory
        if self.taskOne.Image:   self.image = self.taskOne.Image
        if self.taskOne.Command: self.command = ['sh', '-c', ';'.join(self.taskOne.Command)]

    def run2container(self):
        couler.run_container(
            image=self.image,
            command=self.command,
            # args=['sh', '-c'],
            step_name=self.TaskName,
            working_dir=self.working_dir,
            volume_mounts=self.volumes or None,
            input=self.inputs or None,
            output=self.outputs or None,
            resources={"cpu":f"{self.max_cpu}", "memory":self.max_mem+'i'}
        )
        # wf = couler.workflow_yaml()
        # wf["spec"]["templates"][1]["container"]["securityContext"] = securityContext.defineSecurityContext()

class ArgoCouler(Parser_Job):
    Name = "k8s-argo-Couler"
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project):
        self.job_file = job_file
        self.para = parameter
        self.mount_list = []
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.project = project
        self.outdir = outdir
        self.sjm_method = sjm_method
        self.submitter = ArgoSubmitter(namespace="argo")
        self.define_workflow()
        super(ArgoCouler,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)
        self.separate = ";"
        self.connector = '-'
        self.read_file()

    def define_workflow(self):
        print(MyTaskSecurityContext().get_security_context())
        couler.config_workflow(name=f'workflow-{self.project}', service_account='argo')
        couler.states.workflow.set_security_context(securityContext.defineSecurityContext())
        # volume.Volume()

    def write_jobs_to_DAG(self, ):
        all_task_list = self.pipelineGraph.getVertices()
        dag_depend_list = []
        allTaskMounts = []
        for one_a_job in all_task_list:
            onemytask = MyTask(taskOne=one_a_job,name=one_a_job.Name,working_dir=one_a_job.Shell_dir)
            allTaskMounts.append([])
            depend_jobs = self.pipelineGraph.getVertex(one_a_job).prefix
            if depend_jobs:
                couler.set_dependencies(lambda :onemytask.run2container(),
                                             dependencies=' && '.join([job.id.Name+".Succeeded" for job in depend_jobs]))
            else:
                couler.set_dependencies(lambda :onemytask.run2container(),
                                             dependencies=None)
        couler.dag(dag_depend_list)


    def define_sjm_one_job(self, one_job, ):
        pass

    def write_Command_to_file(self):
        """
        重载command，argo-hera模式下不生成shell，但是会将换行+&&更改为";"
        """
        pass

    def create_other_shsh(self):
        pass

    def delivary_pipeline(self, is_run=True, log_file='', guard=True):

        self.outyaml = os.path.join(self.outdir,f'workflow-{self.project}.yaml')
        with open(self.outyaml, 'w') as f_yaml:
            f_yaml.write(pyaml.dump(couler.workflow_yaml(), string_val_style="plain"))

        if is_run:
            couler.run(submitter=self.submitter)
            if guard:
                pass
