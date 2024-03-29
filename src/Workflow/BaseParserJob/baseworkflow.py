#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：STPG 
@File ：baseworkflow.py.py
@Author ：linlin
@Date ：2022/7/11 14:05 
'''
# import os, sys
import copy
import markdown
from typing import List

from lib import get_dict_target
from lib.public_method import *
from lib.graph import DFSGraph as Graph
from lib.tree_dict_display import print_tree
from lib.QC_Result import *

# from Workflow import GlobalPara

pat1 = re.compile('^\s+$')
# pat2 = re.compile('\$\((\S+?)\)(\[\d+\])')
pat2 = re.compile('\{(\S+?)(\[\d+\])\}')
pat3 = re.compile('(Para_[A-Za-z0-9_-]+)\\\\?')
pat4 = re.compile('(DB_[A-Za-z0-9_-]+)\\\\?')
pat5 = re.compile('\S*make\s+')
pat6 = re.compile('\<(\S+?)\>')  # marking output attribute
pat7 = re.compile('/\S+make$')

temp_sub_str1 = random_strings(8)
temp_sub_str2 = random_strings(9)

std = Log(os.path.basename(__file__))

class Output(object):
    def __init__(self):
        pass

class GlobalPara:
    global_sign = 'sign'
    configfile = ''
    def define_sign(self,):
        yamldict = read_yaml(self.configfile)["resource"]
        self.global_sign=yamldict['sign']['finish_sign']
# globalpara = GlobalPara()
# globalpara.define_sign()

class BaseAttribute:
    def __init__(self) -> None:
        self._Code: str = random_strings(12)         # sample(-secondsample) ID
        self.Name: str = ''
        self.Queue: str = ''
        self.CPU: int = 1
        self.Memory: str = ''
        self.Depend: List[str] = []
        self.Command: List[str] = []
        self.QC: List[str] = []
        self.Output: object = object
        self.Input: object = Output()
        self.Abstract: bool = False
        self.Inherit: str = ""
        self.Env: str = ''
        self.Mount: List[str] = []
        self.Image: str = ''
        self.JName: str = ''
        self.Shell_dir: str = ''
        self.Status: str = 'waiting'
        self.Description: str = ''
        self.Part: List[str] = []
        self.SecondPart: List[str] = []
        self.Module: str = ''

class TestBaseAttribute(BaseAttribute):
    """
    test BaseAttribute aviliable
    """
    def test(self) -> None:
        self.Depend = 'test'

class JOB_attribute(BaseAttribute):
    def __init__(self):
        self.key_list = ['Name', 'Env', 'Image', 'Command',
                'Description', 'Part', 'SecondPart', 'QC', 'Mount',
                'Depend', 'Queue', "Status", "Shell_dir",
                'CPU', 'Memory','Output', 'Input', 'Inherit', 'Abstract']
        super(JOB_attribute, self).__init__()

    def addAtribute(self, key, value):
        if key in self.key_list:
            if key in ('Command', 'Part', 'SecondPart'):
                if isinstance(value, str):
                    self.__dict__[key] = [value]
                elif isinstance(value, list):
                    self.__dict__[key] = value
            elif key in ('Depend','Env','Mount'):
                self.__dict__[key].extend(value)
            elif key in ("Output", 'Input') and value:
                if not value: value = {}
                # self.Output = Dict2Obj(value)
                self.__dict__[key] = Dict2Obj(value)
            else:
                if isinstance(value, str):
                    self.__dict__[key] = value.strip()
                else:
                    self.__dict__[key] = value
            return True
        else:
            return False
    
    def updateAtribute(self, key, value):
        self.addAtribute(key, value)

    @property
    def Code(self):
        return self._Code

    @Code.setter
    def Code(self, value):
        self._Code = value

    def format_command(self,sep, global_sign:str = 'finished'):
        # output = ''
        # globalpara.define_sign()
        tt = []
        tt.append('echo ==========start at : `date +"%Y-%m-%d %H:%M:%S"` ==========')
        for i in self.Command:
            i = i.replace('\\\n',temp_sub_str2).replace('\\n',temp_sub_str1)
            annotation_code_line_jurge = i.lstrip(" ").lstrip("\t")
            if annotation_code_line_jurge.startswith("#") and len(annotation_code_line_jurge.split('\n')) < 2:
                continue
            for temp_i in i.split(sep=sep):
                for real_one_cmd in temp_i.split("\n"):
                    annotation_code_line_jurge = real_one_cmd.lstrip(" ").lstrip("\t")
                    if annotation_code_line_jurge.startswith("#"):
                        continue
                    one_cmd = real_one_cmd
                    mm = self.format_string(one_cmd)
                    if " ".join(mm).isspace() or " ".join(mm) == "":continue
                    tt.append(' '.join(mm).replace(temp_sub_str1,'\\n').replace(temp_sub_str2,'\\\n'))
        tt.append('echo ==========end at : `date +"%Y-%m-%d %H:%M:%S"` ==========')
        tt.append('echo {} 1>&2'.format(global_sign))
        tt.append('echo {0} >{1}.{0}'.format(global_sign, os.path.join(self.Shell_dir, '{0}-{1}.sh'.format(self.Module, self.Name))))
        output = f" {sep}".join(tt) + '\n'
        return [len(tt), output]

    def format_string(self, string):
        string = str(string)
        mm = []
        for j in string.split():
            if pat2.search(j):
                j = pat2.sub(r'{\1\2}', j)
            if pat3.search(j):
                j = pat3.sub(r"{para[\1]}", j)
            if pat4.search(j):
                j = pat4.sub(r"{db[\1]}", j)
            mm.append(j)
        return mm

    # @std.logAsDecorator
    def format_para(self, para, init=False, **keyword):
        for key in self.key_list:
            if key in ['Command','Part', 'SecondPart','Mount']: continue
            # if not getattr(self,key,None):continue
            elif key in ['Depend', 'Env', 'QC']:
                format_line_list = []
                for line in getattr(self, key, []):
                    if not line or line == [None]:continue
                    format_line = ' '.join(self.format_string(line))
                    if key == 'QC':
                        try:
                            format_line = format_line.format(**para, **keyword)
                        except Exception as e:
                            # std.warning(e)
                            pass
                    format_line_list.append(format_line)
                setattr(self, key, format_line_list)
            elif key in ['Output', 'Input']:
                if para == {} or keyword == {}: continue
                value = getattr(self, key, None)
                members = [attr for attr in dir(value) if not callable(getattr(value, attr)) and not attr.startswith("__")]
                for member in members:
                    value.__dict__[member] = value.__dict__[member].format(**para, **keyword)
                setattr(self, key, value)
            else:
                value = getattr(self, key, None)
                if value:
                    format_value = ' '.join(self.format_string(value))
                    if key in ['Shell_dir', 'Image'] :
                        if init:continue 
                        setattr(self, key, format_value.format(**para, **keyword))
                    else:
                        setattr(self, key, format_value.format(**para))
    # @std.logAsDecorator
    def format_Part(self, one_part, second_part=[], outdir=""):
        for key in self.key_list:
            if key in ['Depend', 'Env', 'Part', 'SecondPart']:
                format_line_list = []
                for line in getattr(self, key, []):
                    if not line: continue
                    eval_cmd = 'line.format(Part=one_part, SecondPart=second_part)'
                    cmd = eval(eval_cmd)
                    format_line_list.append(cmd)
                setattr(self, key, format_line_list)
            elif key in ['Output', 'Input']:
                value = getattr(self, key, None)
                members = [attr for attr in dir(value) if not callable(getattr(value, attr)) and not attr.startswith("__")]
                for member in members:
                    value.__dict__[member] = value.__dict__[member].format(Part=one_part, SecondPart=second_part)
                setattr(self, key, value)

    def format_Depend(self):
        for key in self.key_list:
            if key == 'Depend':
                for line in getattr(self, key, []):
                    depend_job = line.split(" ")[-1]
    # @property
    def check_mount_exists(self):
        new_mount_list = []
        for mount_pair in self.Mount:
            if os.path.exists(mount_pair.split(":")[0]):
                new_mount_list.append(mount_pair)
        self.Mount = new_mount_list

class TaskOrdinaryTree(Graph):
    """
    重新定义数据结构，从原来的无限字典，更改为图结构
    不能使用树进行定义，详细解释请看：https://blog.csdn.net/luckywinty/article/details/118586087
    """
    pass

class Parser_Job():
    Name = 'baseworkflow'
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method):
        self.pipelineGraph = Graph()
        self.cost = 1 # define weight of graph vertice
        self.job_file = job_file
        self.jobs_dict = {}
        self.jobs_name_map_code = {}
        self.separate = "+++---+++"
        self.connector = '_'
        self.para = parameter
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.globalMSG = object
        self.outdir = outdir
        stpglog = os.path.join(outdir, 'RunSTPG.log')
        if os.path.exists(stpglog):os.remove(stpglog)
        self.STPGLog = Config(stpglog, check=False)
        self.sjm_method = sjm_method
        self.read_file()

    def record_runtime(self, args):
        self.STPGLog.add_a_sector("Para")
        self.STPGLog.add_a_value("Para", "PipelineTemplate", self.job_file)
        self.STPGLog.add_a_value("Para", "PipelineBin", self.pipe_bindir)
        self.STPGLog.add_a_value("Para", "JobList", args.joblist if args.joblist else '')
        self.STPGLog.add_a_value("Para", "ProjectConfig", ','.join(args.config) if args.config else '')
        self.STPGLog.add_a_value("Para", "RunMethod", self.sjm_method)
        self.STPGLog.add_a_value("Para", "EntryPoint", ','.join(args.point) if args.point else '')
        self.STPGLog.add_a_value("Para", "OutDir", self.outdir)
        self.STPGLog.save_msg_change()

    def read_file(self):
        job_tmp_dict,tag, order_list = {}, False,[]
        job_tmp_name = ''

        pipeline_dict = read_yaml(self.job_file)
        self.globalMSG = Yaml2Object(self.job_file).solution(pipeline_dict["resource"])
        default = pipeline_dict["default"]
        self.abstract_jobs = {}
        self.default = Dict2Obj(default)
        error_keys_list = []
        pipeline = pipeline_dict["pipeline"]
        self.pipeline_jobs = multidict()

        for module in pipeline:
            for job in pipeline[module]:
                for i in default:
                    pipeline[module][job].setdefault(i, default[i])
                module_one_job: JOB_attribute = JOB_attribute()
                for key, value in pipeline[module][job].items():
                    back_add_status = module_one_job.addAtribute(key, value)
                    if not back_add_status:error_keys_list.append(key)
                module_one_job.format_para(self.para, init=True)
                if getattr(module_one_job,'Name','') == "":module_one_job.Name = self.replace_jobname(job)
                if module_one_job.Abstract:
                    if module_one_job.Inherit != '' or not module_one_job: 
                        std.error(f'{module_one_job.Name} does not allow both abstract modules and inheritance from other modules')
                    self.abstract_jobs[module_one_job.Name] = pipeline[module][job]
                    continue
                elif module_one_job.Inherit != '':
                    if module_one_job.Inherit not in self.abstract_jobs:                        
                        std.error(f"The abstract class:{module_one_job.Inherit} that this instance job:{module_one_job.Name} depends on does not exist in the flowchart, please check it!!! ")
                    else:
                        new_attribute: dict = copy.deepcopy(self.abstract_jobs[module_one_job.Inherit])
                        input_para_object = new_attribute.pop("Input")
                        [ module_one_job.updateAtribute(key ,value) for key, value in new_attribute.items() ]
                        [ std.error(f'input parameter:{key} not define in instance job') for key in input_para_object.keys() if not hasattr(module_one_job.Input, key) ]
                self.pipeline_jobs[self.replace_jobname(module)][self.replace_jobname(job)] = module_one_job
        modules = list(self.pipeline_jobs.keys())
        self.modules_list = modules

    def obtain_jobset_list(self,list_file):
        list_file_real = obtain_file_realpath(list_file)
        if not list_file_real:return self.modules_list
        joblist_yaml = read_yaml(list_file_real)
        tmp_need_runjob = list(joblist_yaml.keys())
        all_more_set, need_more_set = set_diff_operation(self.modules_list, tmp_need_runjob)
        if need_more_set:
            std.error('The task list contains modules not included in the process,as follows:{0}'.format(need_more_set))
            sys.exit(1)
        if all_more_set:
            std.warning('Please note that the following modules are not analyzed,as follows:{0}'.format(all_more_set))

        return joblist_yaml

    # @std.logAsDecorator
    def clean_pipeline_task(self,need_run_modules):
        self.STPGLog.add_a_sector("ModuleEliminated")
        MainmoduleEliminated, SubmoduleEliminated = '', ''
        for modules in self.modules_list:
            if modules not in need_run_modules:
                std.warning("The main analysis module to be eliminated is:{modules}".format(modules=modules))
                MainmoduleEliminated += ','+modules
                SubmoduleEliminated += ',' + ','.join(list(self.pipeline_jobs[modules].keys()))
                self.pipeline_jobs.pop(modules)
            else:
                for childmodule in list(self.pipeline_jobs[modules].keys()):
                    if need_run_modules[modules] and childmodule not in need_run_modules[modules]:
                        std.warning("The analysis sub module to be eliminated is:{modules}".format(modules=childmodule))
                        SubmoduleEliminated += ','+childmodule
                        self.pipeline_jobs[modules].pop(childmodule)
                    else:
                        pass
        self.modules_list = need_run_modules
        self.STPGLog.add_a_value("ModuleEliminated", "MainmoduleEliminated", MainmoduleEliminated.strip(","))
        self.STPGLog.add_a_value("ModuleEliminated", "SubmoduleEliminated", SubmoduleEliminated.strip(","))

    # @std.logAsDecorator
    def relyon_status_mark(self, module, one_job):
        # globalpara.define_sign()
        markfile = os.path.join(one_job.Shell_dir, '{0}-{1}.sh.{2}'.format(module, one_job.Name, self.globalMSG.sign.finish_sign))
        if os.path.exists(markfile):
            one_job.Status = "done"

    # @std.logAsDecorator
    def define_jobs_order(self,):
        self.pipeline_jobs_name = multidict()
        for modules in self.modules_list:
            for a_job_name in self.pipeline_jobs[modules]:
                a_job = self.pipeline_jobs[modules][a_job_name]
                for index,one_a_job in enumerate(a_job):
                    makedir(one_a_job.Shell_dir)
                    one_a_job.check_mount_exists()
                    self.define_jobs_pub(one_a_job)
                    self.relyon_status_mark(modules, one_a_job)
                    self.pipeline_jobs_name[modules][a_job_name][one_a_job.Name] = index
        del self.jobs_dict
        try:
            self.pipelineGraph.dfs() # define task and prefix relative
        except RecursionError as e:
            std.error(f"Please check whether there is a duplicate module name in the pipeline, or there is a circular dependency between jobs. The specific error message is:{e}")

    # @std.logAsDecorator
    def define_jobs_pub(self,a_job):
        """
        将单个job的依赖从字典视角转换成图视角
        :param a_job: object，单个task
        :return: None
        """
        if a_job.Depend == []: return a_job
        a_job_depend = []
        [a_job_depend.append(i.split(" ")[-1]) for i in a_job.Depend]
        for one_thisjob_depend in a_job_depend:
            one_thisjob_depend = self.replace_jobname(one_thisjob_depend)
            target_path_list = get_dict_target.getpath(self.pipeline_jobs, one_thisjob_depend)
            if  target_path_list and len(target_path_list) >= 2:
                depend_job = self.pipeline_jobs[target_path_list[0]][target_path_list[1]]
                for one_depend_job in depend_job:
                    self.pipelineGraph.addEdge(f=one_depend_job, t=a_job, cost=self.cost)
            elif target_path_list and len(target_path_list) == 1:# main module depend define
                depend_module = self.pipeline_jobs[target_path_list[0]]
                if target_path_list[0] not in self.modules_list:continue
                for childmodule in depend_module:
                    for one_depend_job in depend_module[childmodule]:
                        self.pipelineGraph.addEdge(f=one_depend_job, t=a_job, cost=self.cost)
            else:
                tag = False
                if one_thisjob_depend in self.jobs_name_map_code:
                    self.pipelineGraph.addEdge(f=self.jobs_dict[self.jobs_name_map_code[one_thisjob_depend]], t=a_job, cost=self.cost)
                    tag = True
                else:
                    for itemname, section_config in self.project_config.items():
                        if itemname in ('DB', 'Para') or itemname in a_job.Part: continue
                        for one_value in section_config:
                            real_depend_jobname = one_thisjob_depend + self.connector + str(self.replace_jobname(one_value[0]))
                            if real_depend_jobname in self.jobs_name_map_code:
                                self.pipelineGraph.addEdge(f=self.jobs_dict[self.jobs_name_map_code[real_depend_jobname]], t=a_job, cost=self.cost)
                                tag = True
                            # else:
                            #     std.warning("can not find depend job:{0}".format(real_depend_jobname))
                if not tag:
                    std.warning("remove task:{0} depend module/task:{1}".format(a_job.Name,one_thisjob_depend))
                    a_job.Depend.remove(one_thisjob_depend.replace('-', '_'))

    # @std.logAsDecorator
    def resolution_makefile_unfold(self, cmd_str):
        new_cmd_str, new_cmd_list = '', ['set -e', 'set -v', 'set -o']
        cmd_list = cmd_str.split(' {sep}'.format(sep=self.separate))
        for cmd in cmd_list:
            if pat5.search(cmd) or pat7.search(cmd.split(" ")[0]):
                try:
                    tmp_list = os.popen(cmd + ' -n').readlines()
                    tmp_list[-1] = tmp_list[-1].rstrip()
                    tmp_str = "".join(tmp_list)
                    new_cmd_list.append(tmp_str)
                except IndexError as e:
                    std.error(f"IndexError:{e} list index out of range:{cmd}")
            else:
                new_cmd_list.append(cmd)
        new_cmd_str += ' {sep}'.format(sep=self.separate).join(new_cmd_list)
        new_cmd_str = new_cmd_str.replace(self.separate, ' \n')
        return new_cmd_str

    def replace_jobname(self, a_job_name):
        if self.connector == '_':
            a_job_name = str(a_job_name).replace("-", self.connector)
        elif self.connector == '-':
            a_job_name = str(a_job_name).replace("_", self.connector)
        else:
            a_job_name = a_job_name
        return a_job_name

    # @std.logAsDecorator
    def config_element_iteration(self, config, para, db):
        self.project_config = config
        for modules in self.modules_list:
            for count, a_job_name in enumerate(list(self.pipeline_jobs[modules])):
                a_job = self.pipeline_jobs[modules][a_job_name]
                a_job.Shell_dir = os.path.join(self.outdir, modules, a_job_name) if a_job.Shell_dir == '' else a_job.Shell_dir

                if a_job.Part == []:
                    a_job.Module = modules
                    a_job.JName = a_job_name
                    a_job.format_para(para=para, MainModule=modules, ChildModule=a_job_name, job=a_job)
                    a_job.format_Part('', outdir=self.outdir)
                    try:
                        evaled_cmd = a_job.format_command(sep=self.separate, global_sign=self.globalMSG.sign.finish_sign)[1].format(
                                                                  OUTDIR=self.outdir, BIN=self.pipe_bindir,
                                                                  MainModule=a_job.Module, ChildModule=a_job_name,
                                                                  job=a_job, resource=self.globalMSG,
                                                                  para=para ,db=db)
                    except Exception as e:
                        std.error(f"cmd_template:{a_job.__dict__},error info:{e}")
                    evaled_cmd = self.jobobject_overloading2(evaled_cmd, a_job)
                    cmd = self.resolution_makefile_unfold(evaled_cmd)

                    a_job.Command = [cmd]
                    self.pipeline_jobs[modules][a_job_name] = [a_job]
                    self.jobs_dict[a_job.Code] = a_job
                    self.jobs_name_map_code[a_job.Name] = a_job.Code
                else:
                    run_sample = []
                    for i in a_job.Part:
                        run_sample.extend(config[i])

                    if len(run_sample) > 0:
                        for index, value in enumerate(sorted(run_sample)):
                            if len(a_job.SecondPart) > 0:
                                secondpart = []#[x for x in config[i]]
                                for i in a_job.SecondPart:
                                    secondpart.extend(config[i])
                                if len(secondpart) == 0:continue
                                for one_secondpart in sorted(secondpart):
                                    tmp_a_job = copy.deepcopy(a_job)

                                    tmp_a_job.Module = modules
                                    tmp_a_job.JName = a_job_name
                                    tmp_a_job.Code = random_strings(12)
                                    tmp_a_job.Name = self.connector.join([tmp_a_job.Name, str(self.replace_jobname(value[0])), str(self.replace_jobname(one_secondpart[0]))])
                                    tmp_a_job.format_para(para=para, MainModule=modules, ChildModule=a_job_name, Part=value, SecondPart=one_secondpart, job=tmp_a_job)
                                    tmp_a_job.format_Part(value, second_part=one_secondpart, outdir=self.outdir)
                                    try:
                                        evaled_cmd = tmp_a_job.format_command(sep=self.separate, global_sign=self.globalMSG.sign.finish_sign)[1].format(para=para , Part=value , db=db, SecondPart=one_secondpart,
                                                                                    OUTDIR=self.outdir, BIN=self.pipe_bindir,
                                                                                    MainModule=tmp_a_job.Module,ChildModule=a_job_name, job=tmp_a_job,
                                                                                    resource=self.globalMSG)
                                    except Exception as e:
                                        std.error(f"cmd_template:{tmp_a_job.__dict__},error info:{e}")


                                    evaled_cmd = self.jobobject_overloading2(evaled_cmd, tmp_a_job)
                                    cmd = self.resolution_makefile_unfold(evaled_cmd)

                                    tmp_a_job.Command = [cmd]

                                    if isinstance(self.pipeline_jobs[modules][a_job_name], JOB_attribute):
                                        self.pipeline_jobs[modules][a_job_name] = []
                                    self.pipeline_jobs[modules][a_job_name].append(tmp_a_job)
                                    self.jobs_dict[tmp_a_job.Code] = tmp_a_job
                                    self.jobs_name_map_code[tmp_a_job.Name] = tmp_a_job.Code
                            else:
                                tmp_a_job = copy.deepcopy(a_job)
                                    
                                tmp_a_job.Module = modules
                                tmp_a_job.JName = a_job_name                            
                                tmp_a_job.Name += self.connector + str(self.replace_jobname(value[0]))
                                tmp_a_job.Code = random_strings(12)
                                tmp_a_job.format_para(para=para, MainModule=modules, ChildModule=a_job_name, Part=value, job=tmp_a_job)
                                tmp_a_job.format_Part(value, outdir=self.outdir)
                                try:
                                    evaled_cmd = tmp_a_job.format_command(sep=self.separate, global_sign=self.globalMSG.sign.finish_sign)[1].format(para=para , Part=value ,db=db,
                                                                                OUTDIR=self.outdir, BIN=self.pipe_bindir,
                                                                                MainModule=tmp_a_job.Module,ChildModule=a_job_name, job=tmp_a_job,
                                                                                resource=self.globalMSG)
                                except Exception as e:
                                        std.error(f"cmd_template:{tmp_a_job.__dict__},error info:{e}")

                                evaled_cmd = self.jobobject_overloading2(evaled_cmd, tmp_a_job)
                                cmd = self.resolution_makefile_unfold(evaled_cmd)

                                tmp_a_job.Command = [cmd]
                                if index == 0:
                                    self.pipeline_jobs[modules][a_job_name] = []

                                self.pipeline_jobs[modules][a_job_name].append(tmp_a_job)
                                self.jobs_dict[tmp_a_job.Code] = tmp_a_job
                                self.jobs_name_map_code[tmp_a_job.Name] = tmp_a_job.Code
                    else:
                        std.warning('{} is empty\n'.format(a_job.Part))#, exit_code=1)
                        self.pipeline_jobs[modules].pop(a_job_name)

    def jobobject_overloading2(self, unoverloading_cmd, a_job: JOB_attribute):
        unoverloading_cmd = str(unoverloading_cmd)
        unoverloaded_cmd_list, unoverloaded_cmd_str = [], ''
        unoverloading_cmd_list = unoverloading_cmd.split(' {sep}'.format(sep=self.separate))
        for one_unoverloading_cmd in unoverloading_cmd_list:
            mm = []
            for _, j in enumerate(one_unoverloading_cmd.split(sep=" ")):
                if pat6.search(j):
                    one_loading_obj = pat6.search(j).group(1).split("Output")[0].strip('.')
                    j = self.replace_jobname(pat6.sub(r"{\1}", j))

                    input_task_dir = get_dict_target.getpath(self.pipeline_jobs, self.replace_jobname(one_loading_obj))
                    if input_task_dir:
                        if len(input_task_dir) == 1: std.error(
                            "Output cannot be set for main task:{0}".format(input_task_dir[0]))
                        all_input_tasks = self.pipeline_jobs[input_task_dir[0]][input_task_dir[1]]
                        j_multiple_str = j.strip().split("=")[0] + "="
                        j_multiple_list = []
                        for input_task in all_input_tasks:
                            j_tmp = j.replace(one_loading_obj, input_task.Code)
                            j_tmp = eval("j_tmp.format({TaskCode}=self.jobs_dict[input_task.Code])".format(
                                TaskCode=input_task.Code))
                            j_multiple_list.append(j_tmp.strip().split("=")[-1])
                        a_job.Input.MultiInput1 = j_multiple_list
                        if len(j.strip().split("=")) == 2:
                            j_multiple_str += ",".join(j_multiple_list)
                        elif len(j.strip().split("=")) == 1:
                            j_multiple_str = ",".join(j_multiple_list)
                        j = j_multiple_str
                    else:
                        one_loading_obj = self.replace_jobname(one_loading_obj)
                        if a_job.Part != [] and one_loading_obj not in self.jobs_name_map_code:#len(j.strip().split("=")) >= 2:
                            j_multiple_str = j.strip().split("=")[0] + "="
                            j_multiple_list = []
                            for itemname, one_secondvalues in self.project_config.items():
                                if itemname in ('DB', 'Para') or itemname in a_job.Part:continue
                                for secondvalue in one_secondvalues:
                                    secondvalueFirstElement = self.replace_jobname(secondvalue[0])
                                    defindedOneJob = one_loading_obj + self.connector + secondvalueFirstElement
                                    if defindedOneJob in self.jobs_name_map_code:
                                        defindedOneJobCode = self.jobs_name_map_code.get(defindedOneJob)
                                        j_tmp = j.replace(one_loading_obj.replace('-',"_"), defindedOneJobCode)
                                        j_tmp = eval("j_tmp.format({TaskCode}=self.jobs_dict[defindedOneJobCode])".format(
                                            TaskCode=defindedOneJobCode))
                                        j_multiple_list.append(j_tmp.strip().split("=")[-1])
                            a_job.Input.MultiInput2 = j_multiple_list
                            if '=' in j:
                                j += ",".join(j_multiple_list)
                            else:
                                j = ",".join(j_multiple_list)
                        else:
                            try:
                                defindedOneJobCode = self.jobs_name_map_code.get(one_loading_obj, 'uncertain')
                                j = j.replace(one_loading_obj.replace('-', "_"), defindedOneJobCode)
                                j = eval("j.format({TaskCode}=self.jobs_dict[defindedOneJobCode])".format(
                                    TaskCode=defindedOneJobCode))
                                a_job.Input.SingleInput1 = j
                            except KeyError as e:
                                std.warning(f"{one_loading_obj}:{e} not in pipeline graph,this command line is:{j}:{one_unoverloading_cmd}")
                mm.append(j)
            unoverloaded_cmd = " ".join(mm)
            unoverloaded_cmd_list.append(unoverloaded_cmd)
        # unoverloaded_cmd_str = ' {sep}'.format(sep=self.separate).join(unoverloaded_cmd_list)#.replace('\\ &&\\','\\')
        unoverloaded_cmd_str = ' {sep}'.format(sep=self.separate).join(unoverloaded_cmd_list)#.replace('\\ &&\\','\\')
        return unoverloaded_cmd_str

    def write_Command_to_file(self):
        # 从图中获取所有task信息
        allTaskObject = self.pipelineGraph.getVertices()
        for taskObject in allTaskObject:
            self.write_object_job(taskObject.Module, taskObject)

    def write_object_job(self,modules, one_job):
        shell_basename = '{0}-{1}'.format(modules, one_job.Name)
        shsh = os.path.join(one_job.Shell_dir, shell_basename) + '.sh'
        with open(shsh, 'w') as f:
            f.write('\n'.join(one_job.Command))


    def get_jobs_mainbody(self):
        pass

    def change_to_startpoint(self, startpoints):
        if startpoints:
            std.info("Startpoint: ...")
            std.info('\tfrom %s\n' % ', '.join(startpoints))
            for eachstart in startpoints:
                eachstart_path_list = get_dict_target.getpath(self.pipeline_jobs, eachstart)
                if not eachstart_path_list:
                    std.error('POINT ' + eachstart + ' not in you analysis, Please check your script!\nAvailable POINTS are:\n' + print_tree(self.pipeline_jobs) + '\n')
                    sys.exit(1)
                if len(eachstart_path_list) == 2:
                    eachstart_job = self.pipeline_jobs[eachstart_path_list[0]][eachstart_path_list[1]]
                    self.change_upstream_status(eachstart_job, [])
                    self.change_downstream_status(eachstart_job)
                elif len(eachstart_path_list) == 1:
                    alreadychange = []
                    for childmodule in self.pipeline_jobs[eachstart_path_list[0]]:
                        eachstart_job = self.pipeline_jobs[eachstart_path_list[0]][childmodule]
                        self.change_upstream_status(eachstart_job, alreadychange)
                        self.change_downstream_status(eachstart_job)
                        alreadychange.extend(eachstart_job)

    def change_downstream_status(self,one_task):
        if not one_task or one_task == []:return
        for one_point_task in one_task:
            taskvertext = self.pipelineGraph.getVertex(one_point_task)
            if not taskvertext:return
            downsteam_tasklist = taskvertext.getConnections()
            for downsteam_task in downsteam_tasklist:
                downsteam_task.id.Status = "waiting"
            self.change_downstream_status([downsteam_task.id for downsteam_task in downsteam_tasklist ])

    def change_upstream_status(self,one_job, alreadychange=[]):
        for one_one_job in one_job:
            one_one_job.Status = 'waiting'
            routeUpstreamTask = self.pipelineGraph.getUpstreamVertex(one_one_job)
            for one_routeUpstreamTask in routeUpstreamTask:
                if one_routeUpstreamTask not in alreadychange:
                    one_routeUpstreamTask.Status = 'done'

    def delivary_pipeline(self, is_run=False):
        std.info("该模块为任务投递模块，每一个投递子类需要继承并重写")

    def Run_QualityControl(self,):
        css = '''
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<style type="text/css">
<!-- 此处省略掉markdown的css样式，因为太长了 -->
</style>
        '''
        QC_Content = '# '+self.project+' Automatic Quality Control Report  \n'
        qcmethod = QC_Method(self.globalMSG, '')
        for modules in self.pipeline_jobs:
            qc_ishave_tag = True
            tmp_qc_content_first = '## '+ modules + '\n'
            for jobs in self.pipeline_jobs[modules]:
                tmp_qc_content_second = '### ' + jobs + '\n'
                one_job = self.pipeline_jobs[modules][jobs]
                for one_one_job in one_job:
                    if one_one_job.QC == []:
                        qc_ishave_tag = False
                    else:
                        for oneqc_file in one_one_job.QC:
                            qcmethod.BuildObject(oneqc_file)
                            qcmethod.QC_Content()
                            tmp_qc_content_second += qcmethod.QC_Result
                if tmp_qc_content_second != '### ' + jobs + '\n':
                    tmp_qc_content_first += tmp_qc_content_second
            if tmp_qc_content_first != '## '+ modules + '\n':
                QC_Content += tmp_qc_content_first
        ## markdown convert to html
        QC_HTML = markdown.markdown(QC_Content)
        OutQcfile = os.path.join(self.outdir, self.project+'.QC_Result.html')
        with open(OutQcfile, 'w', encoding="utf-8",errors="xmlcharrefreplace") as O_fi:
            O_fi.write(css+QC_HTML)

    def Mount_new_disk(self, waiting_check_list):
        for onecheck in waiting_check_list:
            if not onecheck:continue
            if isinstance(onecheck, list):
                self.Mount_new_disk(onecheck)
            elif isinstance(onecheck, str):
                onecheck = onecheck.rstrip("/")
                if os.path.exists(onecheck):
                    if os.path.isfile(onecheck):
                        onecheck = os.path.dirname(onecheck)
                    onecheck_splited = onecheck.split("/")
                    if len(onecheck_splited) < 2:
                        std.warning("The path is the root directory, and automatic mounting is not performed:"+onecheck)
                        continue
                    new_mount_str = '/'.join(onecheck_splited[:3]) + ":" + '/'.join(onecheck_splited[:3]) + ":ro"
                    # if new_mount_str not in self.mount_list:
                    #     self.mount_list.append(new_mount_str)
            else:
                std.error("The configuration file information is abnormal. Please check it,{0}".format(onecheck))
    
    def write_jobs_to_DAG(self):
        pass



