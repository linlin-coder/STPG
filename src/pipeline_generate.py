# -*- coding: gbk -*-

import argparse
import copy
import os,re
import sys
import markdown

bin_tool = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(bin_tool,'lib'))
from lib import get_dict_target
from lib.authority import Authorize, AuthorCode
from lib.public_method import *
from lib.graph import DFSGraph as Graph
from lib.tree_dict_display import print_tree
from lib.QC_Result import *

std = Log(os.path.basename(__file__))

from Workflow.version import __author__, __date__, __mail__, tool_bin
from Workflow import GlobalPara

globalpara = GlobalPara()
'''
1. �ó�����config.ini ��job.template��job.listΪ�������ɷ�������
'''

pat1 = re.compile('^\s+$')
# pat2 = re.compile('\$\((\S+?)\)(\[\d+\])')
pat2 = re.compile('\{(\S+?)(\[\d+\])\}')
pat3 = re.compile('(Para_[A-Za-z0-9_-]+)\\\\?')
pat4 = re.compile('(DB_[A-Za-z0-9_-]+)\\\\?')
pat5 = re.compile('\S*make\s')
pat6 = re.compile('\<(\S+?)\>')  # marking output attribute
ReserveWord = ['OUTDIR','BIN','LOGFILE']

class Output(object):
    def __init__(self):
        pass

class JOB_attribute():
    def __init__(self):
        self.Name = ''
        self.Queue = ''
        self.CPU = 1
        self.Memory = "1G"
        self.Depend = []
        self.Command = []
        self.QC = []
        self.Output = Output()
        self.Env = ""
        self.Mount = []
        self.Image = ""
        self.JName = ''
        self.Shell_dir = ""
        self.Status = "waiting"
        self.Description = ''
        self.Part = []
        self.Module = ''
        self.key_list = ['Name', 'Env', 'Image', 'Command',
                'Description', 'Part', 'QC', 'Mount',
                'Depend', 'Queue', "Status", "Shell_dir",
                'CPU', 'Memory','Output']#'sched_options',
        # super(Deliver_DAG_Job,self).__init__('', '')

    def addAtribute(self, key, value):
        if key in self.key_list:
            if key in ('Command','Part'):
                if isinstance(value, str):
                    self.__dict__[key] = [value]
                elif isinstance(value, list):
                    self.__dict__[key] = value
            elif key in ('Depend','Env','Mount'):
                self.__dict__[key].extend(value)
            elif key == "Output" and value:
                if not value: value = {}
                self.Output = Dict2Obj(value)
            else:
                if isinstance(value, str):
                    self.__dict__[key] = value.strip()
                else:
                    self.__dict__[key] = value
            return True
        else:
            return False

    def format_command(self):
        output = ''
        globalpara.define_sign()
        tt = []
        tt.append('echo ==========start at : `date +"%Y-%m-%d %H:%M:%S"` ==========')
        # print(self.Command)
        for i in self.Command:
            mm = self.format_string(i)
            tt.append(" ".join(mm))
        tt.append('echo ==========end at : `date +"%Y-%m-%d %H:%M:%S"` ==========')
        tt.append('echo {} 1>&2'.format(globalpara.global_sign))
        tt.append('echo {0} >$0.{0}'.format(globalpara.global_sign))
        output = " &&\\\n".join(tt) + '\n'
        # print(output)
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

    def format_para(self, para, **keyword):
        for key in self.key_list:
            if key in ['Command','Part','Mount']: continue
            # if not getattr(self,key,None):continue
            elif key in ['Depend', 'Env', 'QC']:
                format_line_list = []
                for line in getattr(self, key, []):
                    # print('a',line)
                    if not line or line == [None]:continue
                    format_line = ' '.join(self.format_string(line))
                    format_line_list.append(format_line)
                setattr(self, key, format_line_list)
            elif key in ['Output', ]:
                if para == {} or keyword == {}: continue
                value = getattr(self, key, None)
                members = [attr for attr in dir(value) if not callable(getattr(value, attr)) and not attr.startswith("__")]
                for member in members:
                    value.__dict__[member] = value.__dict__[member].format(**para, **keyword)
            else:
                value = getattr(self, key, None)
                if value:
                    format_value = ' '.join(self.format_string(value))
                    setattr(self, key, format_value.format(**para))

    def format_Part(self, one_part, outdir=""):
        for key in self.key_list:
            if key in ['Depend', 'Env', 'Part']:
                format_line_list = []
                for line in getattr(self, key, []):
                    if not line: continue
                    eval_cmd = 'line.format(Part=one_part)'
                    cmd = eval(eval_cmd)
                    format_line_list.append(cmd)
                setattr(self, key, format_line_list)
            elif key in ['Output',]:
                value = getattr(self, key, None)
                members = [attr for attr in dir(value) if not callable(getattr(value, attr)) and not attr.startswith("__")]
                for member in members:
                    value.__dict__[member] = value.__dict__[member].format(Part=one_part)

    def format_Depend(self):
        for key in self.key_list:
            if key == 'Depend':
                for line in getattr(self, key, []):
                    depend_job = line.split(" ")[-1]

class TaskOrdinaryTree(Graph):
    """
    ���¶������ݽṹ����ԭ���������ֵ䣬����Ϊͼ�ṹ
    ����ʹ�������ж��壬��ϸ�����뿴��https://blog.csdn.net/luckywinty/article/details/118586087
    """
    pass

class Parser_Job():#Deliver_DAG_Job):
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method):
        self.pipelineGraph = Graph()
        self.cost = 1 # define weight of graph vertice
        self.job_file = job_file
        self.jobs_dict = {}
        # self.project_configdir = args.config
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
        # super(Parser_Job,self).__init__(sjm_method)

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
        self.globalMSG = Yaml2Object().solution(pipeline_dict["resource"])
        default = pipeline_dict["default"]
        self.default = Dict2Obj(default)
        error_keys_list = []
        pipeline = pipeline_dict["pipeline"]

        for module in pipeline:
            for job in pipeline[module]:
                for i in default:
                    pipeline[module][job].setdefault(i, default[i])
                module_one_job = JOB_attribute()
                for key, value in pipeline[module][job].items():
                    back_add_status = module_one_job.addAtribute(key, value)
                    if not back_add_status:error_keys_list.append(key)
                module_one_job.format_para(self.para)
                if getattr(module_one_job,'Name','') == "":module_one_job.Name = job
                pipeline[module][job] = module_one_job
        modules = list(pipeline.keys())
        self.pipeline_jobs = pipeline
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

    def relyon_status_mark(self, module, one_job):
        globalpara.define_sign()
        markfile = os.path.join(one_job.Shell_dir, '{0}-{1}.sh.{2}'.format(module, one_job.Name, globalpara.global_sign))
        if os.path.exists(markfile):
            one_job.Status = "done"

    def define_jobs_order(self,):
        self.pipeline_jobs_name = multidict()
        for modules in self.modules_list:
            for a_job_name in self.pipeline_jobs[modules]:
                a_job = self.pipeline_jobs[modules][a_job_name]
                for index,one_a_job in enumerate(a_job):
                    makedir(one_a_job.Shell_dir)
                    self.define_jobs_pub(one_a_job)
                    self.relyon_status_mark(modules, one_a_job)
                    self.pipeline_jobs_name[modules][a_job_name][one_a_job.Name] = index
        del self.jobs_dict
        self.pipelineGraph.dfs() # define task and prefix relative

    def define_jobs_pub(self,a_job):
        """
        ������job���������ֵ��ӽ�ת����ͼ�ӽ�
        :param a_job: object������task
        :return: None
        """
        if a_job.Depend == []: return a_job
        a_job_depend = []
        [a_job_depend.append(i.split(" ")[-1]) for i in a_job.Depend]
        for one_thisjob_depend in a_job_depend:
            target_path_list = get_dict_target.getpath(self.pipeline_jobs, one_thisjob_depend)
            if  target_path_list and len(target_path_list) >= 2:
                depend_job = self.pipeline_jobs[target_path_list[0]][target_path_list[1]]
                for one_depend_job in depend_job:
                    self.pipelineGraph.addEdge(f=one_depend_job, t=a_job, cost=self.cost)
            elif target_path_list and len(target_path_list) == 1:# main module depend define
                depend_module = self.pipeline_jobs[target_path_list[0]]
                # a_job.Depend.remove('{0}'.format(target_path_list[0]))
                if target_path_list[0] not in self.modules_list:continue
                for childmodule in depend_module:
                    for one_depend_job in depend_module[childmodule]:
                        self.pipelineGraph.addEdge(f=one_depend_job, t=a_job, cost=self.cost)
            else:
                tag = False
                if one_thisjob_depend in self.jobs_dict:
                    self.pipelineGraph.addEdge(f=self.jobs_dict[one_thisjob_depend], t=a_job, cost=self.cost)
                    tag = True
                if not tag:
                    std.warning("remove task:{0} depend module/task:{1}".format(a_job.Name,one_thisjob_depend))
                    a_job.Depend.remove(one_thisjob_depend)

    def resolution_makefile_unfold(self, cmd_str):
        return cmd_str
        new_cmd_str, new_cmd_list = '', ['set -e', 'set -o']
        cmd_list = cmd_str.split(' &&\\\n')
        for cmd in cmd_list:
            if pat5.search(cmd):
                tmp_list = os.popen(cmd + ' -n').readlines()
                tmp_list[-1] = tmp_list[-1].rstrip()
                tmp_str = "".join(tmp_list)
                new_cmd_list.append(tmp_str)
            else:
                new_cmd_list.append(cmd)
        new_cmd_str += ' &&\\\n'.join(new_cmd_list)
        return new_cmd_str

    def config_element_iteration(self, config, para, db):
        self.project_config = config
        make = 'make'
        for modules in self.modules_list:
            for count, a_job_name in enumerate(list(self.pipeline_jobs[modules])):
                a_job = self.pipeline_jobs[modules][a_job_name]
                a_job.Shell_dir = os.path.join(self.outdir, modules, a_job_name)
                if a_job.Part == []:
                    a_job.Module = modules
                    evaled_cmd = a_job.format_command()[1].format(OUTDIR=self.outdir, BIN=self.pipe_bindir,
                                                                  MainModule=a_job.Module, ChildModule=a_job_name,
                                                                  job=a_job, resource=self.globalMSG,
                                                                  para=para ,db=db)
                    # evaled_cmd = eval(eval_cmd)
                    evaled_cmd = self.jobobject_overloading2(evaled_cmd)
                    cmd = self.resolution_makefile_unfold(evaled_cmd)

                    a_job.Command = [cmd]
                    a_job.JName = a_job_name
                    a_job.format_para(para=para, MainModule=modules, ChildModule=a_job_name)
                    a_job.format_Part('', outdir=self.outdir)
                    self.pipeline_jobs[modules][a_job_name] = [a_job]
                    self.jobs_dict[a_job.Name] = a_job
                else:
                    run_sample = []
                    for i in a_job.Part:
                        run_sample.extend(config[i])
                    #run_sample.extend([ config[i] for i in a_job.Part ])
                    # pre_job_count = 0

                    if len(run_sample) > 0:
                        for index, value in enumerate(sorted(run_sample)):
                            tmp_a_job = copy.copy(a_job)
                            tmp_a_job.Module = modules
                            evaled_cmd = tmp_a_job.format_command()[1].format(para=para , Part=value ,db=db,
                                                                              OUTDIR=self.outdir, BIN=self.pipe_bindir,
                                                                              MainModule=tmp_a_job.Module,ChildModule=a_job_name, job=tmp_a_job,
                                                                              resource=self.globalMSG)
                            # evaled_cmd = eval(eval_cmd)
                            evaled_cmd = self.jobobject_overloading2(evaled_cmd)
                            cmd = self.resolution_makefile_unfold(evaled_cmd)
                            value[0] = str(value[0]).replace("-", "_")

                            tmp_a_job.Name += '_' + str(value[0])
                            tmp_a_job.Command = [cmd]
                            tmp_a_job.JName = a_job_name
                            tmp_a_job.format_para(para=para, MainModule=modules, ChildModule=a_job_name, Part=value)
                            tmp_a_job.format_Part(value, outdir=self.outdir)
                            if index == 0:
                                self.pipeline_jobs[modules][a_job_name] = []

                            self.pipeline_jobs[modules][a_job_name].append(tmp_a_job)
                            self.jobs_dict[tmp_a_job.Name] = tmp_a_job
                    else:
                        std.warning('{} is empty\n'.format(a_job.Part))#, exit_code=1)
                        self.pipeline_jobs[modules].pop(a_job_name)
        # del self.jobs_dict
        # return jobs

    def jobobject_overloading2(self, unoverloading_cmd):
        unoverloading_cmd = str(unoverloading_cmd)
        unoverloaded_cmd_list, unoverloaded_cmd_str = [], ''
        unoverloading_cmd_list = unoverloading_cmd.split(' &&\\\n')
        for one_unoverloading_cmd in unoverloading_cmd_list:
            mm = []
            for com_sub_index, j in enumerate(one_unoverloading_cmd.split()):
                if pat6.search(j):
                    one_loading_obj = pat6.search(j).group(1).split(".")[0]
                    j = pat6.sub(r"{\1}", j)

                    input_task_dir = get_dict_target.getpath(self.pipeline_jobs, one_loading_obj)
                    if input_task_dir:
                        if len(input_task_dir) == 1: std.error(
                            "Output cannot be set for main task:{0}".format(input_task_dir[0]))
                        all_input_tasks = self.pipeline_jobs[input_task_dir[0]][input_task_dir[1]]
                        j_multiple_str = j.strip().split("=")[0] + "="
                        j_multiple_list = []
                        for input_task in all_input_tasks:
                            j_tmp = j.replace(one_loading_obj, input_task.Name)
                            j_tmp = eval("j_tmp.format({one_loading_obj}=self.jobs_dict[input_task.Name])".format(
                                one_loading_obj=input_task.Name))
                            j_multiple_list.append(j_tmp.strip().split("=")[-1])
                        j_multiple_str += ",".join(j_multiple_list)
                        j = j_multiple_str
                    else:
                        j = eval("j.format({one_loading_obj}=self.jobs_dict[one_loading_obj])".format(
                            one_loading_obj=one_loading_obj))
                mm.append(j)
            unoverloaded_cmd = " ".join(mm)
            unoverloaded_cmd_list.append(unoverloaded_cmd)
        unoverloaded_cmd_str = ' &&\\\n'.join(unoverloaded_cmd_list)
        return unoverloaded_cmd_str

    def write_Command_to_file(self):
        # ��ͼ�л�ȡ����task��Ϣ
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
                downsteam_task.Status = "waiting"
                self.change_downstream_status([downsteam_task])

    def change_upstream_status(self,one_job, alreadychange=[]):
        for one_one_job in one_job:
            one_one_job.Status = 'waiting'
            routeUpstreamTask = self.pipelineGraph.getUpstreamVertex(one_one_job)
            for one_routeUpstreamTask in routeUpstreamTask:
                if one_routeUpstreamTask not in alreadychange:
                    one_routeUpstreamTask.Status = 'done'

    def delivary_pipeline(self, is_run=False):
        std.info("��ģ��Ϊ����Ͷ��ģ�飬ÿһ��Ͷ��������Ҫ�̳в���д")

    def Run_QualityControl(self,):
        css = '''
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<style type="text/css">
<!-- �˴�ʡ�Ե�markdown��css��ʽ����Ϊ̫���� -->
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
                    if new_mount_str not in self.mount_list:
                        self.mount_list.append(new_mount_str)
            else:
                std.error("The configuration file information is abnormal. Please check it,{0}".format(onecheck))

def main():

    ##################Permission verification##############
    author_handle = Authorize(toolbin=bin_tool + '/../')
    CheckStatus, residueday = author_handle.checkAuthored()
    if CheckStatus == AuthorCode.Author_right:
        pass
    elif CheckStatus == AuthorCode.Author_overtime:
        std.warning("Authorization timeout, please reactivate!!!")
        regist_state = author_handle.regist()
        if not regist_state:
            std.fatal("Activation failed!!!")
    elif CheckStatus == AuthorCode.Author_NoneDecode:
        std.warning("Activation file information error!!!")
        regist_state = author_handle.regist()
        if not regist_state:
            std.fatal("Activation failed!!!")
    elif CheckStatus == AuthorCode.Author_NoneRegist:
        std.warning("No active file")
        regist_state = author_handle.regist()
        if not regist_state:
            std.fatal("Activation failed!!!")
    # elif CheckStatus == AuthorCode.:
    print("residueday:", residueday, "days")
    ###########################################################

    parser = argparse.ArgumentParser(description='', formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='author:\t{0}\nmail:\t{1}\ndate:\t{2}\n'.format(__author__, __mail__,__date__))

    parser.add_argument('-b', '--bin', help='pipeline bindir',dest='bindir', required=True,)
    parser.add_argument('-c', '--config', help='project config',dest='config', required=True,nargs="+")
    parser.add_argument('-pro', '--project', help='analysis project id', dest='project',default='Test')
    parser.add_argument('-p', '--point', help='startpoint', dest='point',nargs="+")
    parser.add_argument('-t', '--template', help='template file', dest='template',required=True)
    parser.add_argument('-l', '--list', help='job list file', dest='joblist')
    parser.add_argument('-m', '--method', help='run job method using SJM', dest='method',default='singularity',
                        choices=['sge-singularity-sjm','sge-docker-sjm','sge-normal-sjm','k8s-docker-argo'])
    parser.add_argument('-r', '--run', help='run analysis pipeline', dest='run',action='store_true')
    parser.add_argument('-o', '--outdir', help='analysis result outdir', dest='outdir',type=str)

    args = parser.parse_args()
    #parameter deal
    makedir(args.outdir)
    outdir = obtain_file_realpath(args.outdir)
    pipe_bindir = obtain_file_realpath(args.bindir)

    ## tool config read
    GlobalPara.configfile = args.template
    ## parser project-config-ini
    project_config, project_para, project_db, project_orders = ReadConfig(args.config)
    if 'BIN' not in project_para:
        project_para['BIN'] = pipe_bindir
        project_para['OUTDIR'] = outdir
    if args.method == "sge-docker-wdl":
        from Workflow.Cromwell.WDL_workflow import WDL_Workflow
        ReadJob = WDL_Workflow(job_file=args.template, parameter=project_para,outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method)
    elif "sjm" in args.method:
        from Workflow.SGE_SJM.SJM_DAG import SJM_Job
        ReadJob = SJM_Job(job_file=args.template, parameter=project_para,outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method, project=args.project)
    elif "argo" in args.method:
        from Workflow.K8S_argo.argo_workflow import ARGO_workflow
        ReadJob = ARGO_workflow(job_file=args.template, parameter=project_para, outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method, project=args.project)
        # volumeMounts = ReadJob.ascertain_data_mount()
        # ReadJob.get_dependence()
        # ReadJob.write_Command_to_file()
        # ReadJob.DAG2yaml(dependence_dict, shell_dir=outdir, jobname=args.project,)
        # ReadJob.delivary_pipeline(yaml_file='.')
    else:
        ReadJob = Parser_Job(job_file=args.template, parameter=project_para,outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method)
    # ReadJob.read_file()
    ReadJob.config_element_iteration(project_config, project_para, project_db)
    if args.joblist:
        need_run_modules = ReadJob.obtain_jobset_list(args.joblist)
        ReadJob.clean_pipeline_task(need_run_modules)
    ReadJob.define_jobs_order()
    if args.point:
        startpoints = [str(x) for x in args.point]
        ReadJob.change_to_startpoint(startpoints)
    ReadJob.write_Command_to_file()

    # Mount the default unmounted path into the container, waiting develop
    mountCheckList = copy.copy(project_config['sample'])
    mountCheckList.append(list(project_db.values()))
    mountCheckList.append(list(project_para.values())+[outdir])
    ReadJob.Mount_new_disk(mountCheckList)

    # write dag file by enginer
    ReadJob.write_jobs_to_DAG()
    # create others file of running need
    ReadJob.create_other_shsh()
    ReadJob.record_runtime(args=args)
    ReadJob.delivary_pipeline(is_run=args.run)
    ReadJob.Run_QualityControl()

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print(__doc__)
        sys.exit(1)

    main()
