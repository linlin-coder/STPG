# -*- coding: gbk -*-

import argparse
import copy
import os
import sys

bin_tool = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(bin_tool,'lib'))
from lib import get_dict_target
from lib.public_method import *
from lib.tree_dict_display import print_tree

std = Log(os.path.basename(__file__))

from Workflow.version import __author__, __date__, __mail__, tool_bin
from Workflow import GlobalPara

globalpara = GlobalPara()
'''
1. 该程序以config.ini 、job.template和job.list为依赖生成分析流程
'''

pat1 = re.compile('^\s+$')
# pat2 = re.compile('\$\((\S+?)\)(\[\d+\])')
pat2 = re.compile('\{(\S+?)(\[\d+\])\}')
pat3 = re.compile('(Para_[A-Za-z0-9_-]+)\\\\?')
pat4 = re.compile('(DB_[A-Za-z0-9_-]+)\\\\?')
pat5 = re.compile('\S*make\s')
ReserveWord = ['OUTDIR','BIN','LOGFILE']

class JOB_attribute():
    def __init__(self):
        self.Name = ''
        self.Queue = ''
        self.CPU = 1
        self.Memory = "1G"
        # self.sched_options = '' # 取消sjm独有的投递资源属性
        self.Depend = []
        self.Command = []
        self.Env = ""
        self.Image = ""
        self.Shell_dir = ""
        self.Status = "waiting"
        self.Description = ''
        self.Part = ''
        self.Module = ''
        self.key_list = ['Name', 'Env', 'Image', 'Command',
                'Description', 'Part',
                'Depend', 'Queue', "Status", "Shell_dir",
                'CPU', 'Memory']#'sched_options',
        # super(Deliver_DAG_Job,self).__init__('', '')

    def addAtribute(self, key, value):
        if key in self.key_list:
            if key == 'Command':
                if isinstance(value, str):
                    self.__dict__[key] = [value]
                elif isinstance(value, list):
                    self.__dict__[key] = value
            elif key in ('Depend'):
                # dependencies = re.split(';|,', value.strip())
                # for depend in dependencies:
                #     if depend.strip(): self.__dict__[key].append(depend)
                self.__dict__[key].extend(value)
            elif key in ('Env'):
                self.__dict__[key].extend(value)
            # elif key == 'Memory':
            #     self.__dict__[key] = value.strip().rstrip('gG')
            # 可以为小数
            # if not value.isdigit():
            #    std.fatal('{} memory should not have unit'.format(value),exit_code=1)
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
            # for i in ReserveWord:
            #     j = j.replace(i, '{{{0}}}'.format(i))
            mm.append(j)
        return mm

    def format_para(self, para):
        for key in self.key_list:
            if key in ['Command']: continue
            # if not getattr(self,key,None):continue
            if key in ['Depend', 'Env']:
                format_line_list = []
                for line in getattr(self, key, []):
                    # print('a',line)
                    if not line or line == [None]:continue
                    format_line = ' '.join(self.format_string(line))
                    # print('b',format_line)
                    format_line_list.append(format_line)
                    # print('c',format_line_list)
                setattr(self, key, format_line_list)
            else:
                value = getattr(self, key, None)
                if value:
                    format_value = ' '.join(self.format_string(value))
                    setattr(self, key, format_value.format(**para))

    def format_Part(self,one_part):
        for key in self.key_list:
            if key in ['Depend', 'Env']:
                format_line_list = []
                for line in getattr(self, key, []):
                    if not line:continue
                    # format_line_list.append(line.format(Part=one_part))
                    eval_cmd = 'line.format(Part=one_part)'
                    cmd = eval(eval_cmd)
                    format_line_list.append(cmd)
                setattr(self, key, format_line_list)

    def format_Depend(self):
        for key in self.key_list:
            if key == 'Depend':
                for line in getattr(self, key, []):
                    depend_job = line.split(" ")[-1]


class Parser_Job():#Deliver_DAG_Job):
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method):
        self.job_file = job_file
        # self.project_configdir = args.config
        self.para = parameter
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.outdir = outdir
        self.sjm_method = sjm_method
        self.read_file()
        # super(Parser_Job,self).__init__(sjm_method)

    def read_file(self):
        job_tmp_dict,tag, order_list = {}, False,[]
        job_tmp_name = ''

        pipeline_dict = read_yaml(self.job_file)
        default = pipeline_dict["default"]
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
        tmp_need_runjob = []
        list_file_real = obtain_file_realpath(list_file)
        if not list_file_real:return self.modules_list
        # with open(list_file_real, 'r') as f_jobs:
        #     for line in f_jobs.readlines():
        #         if line.startswith("#"):continue
        #         job = line.split(" ")
        #         if len(job) > 1:
        #             std.warning('joblist:{0},There is a problem with the format,line content is:{1},use first element {2}'.format(list_file_real, line, job[0]))
        #         if job[0] not in tmp_need_runjob:tmp_need_runjob.append(job[0])
        joblist_yaml = read_yaml(list_file_real)
        tmp_need_runjob = list(joblist_yaml.keys())
        all_more_set, need_more_set = set_diff_operation(self.modules_list, tmp_need_runjob)
        if need_more_set:
            std.error('The task list contains modules not included in the process,as follows:{0}'.format(need_more_set))
            sys.exit(1)
        if all_more_set:
            std.warning('Please note that the following modules are not analyzed,as follows:{0}'.format(all_more_set))

        # return tmp_need_runjob
        return joblist_yaml

    def clean_pipeline_task(self,need_run_modules):
        for modules in self.modules_list:
            if modules not in need_run_modules:
                std.warning("The main analysis module to be eliminated is:{modules}".format(modules=modules))
                self.pipeline_jobs.pop(modules)
            else:
                for childmodule in list(self.pipeline_jobs[modules].keys()):
                    if need_run_modules[modules] and childmodule not in need_run_modules[modules]:
                        std.warning("The analysis sub module to be eliminated is:{modules}".format(modules=childmodule))
                        self.pipeline_jobs[modules].pop(childmodule)
                    else:
                        pass
        self.modules_list = need_run_modules

    def relyon_status_mark(self, module, one_job):
        globalpara.define_sign()
        markfile = os.path.join(one_job.Shell_dir, '{0}-{1}.sh.{2}'.format(module, one_job.Name, globalpara.global_sign))
        if os.path.exists(markfile):
            one_job.Status = "done"

    def define_jobs_order(self,):
        for modules in self.modules_list:
            for a_job_name in self.pipeline_jobs[modules]:
                a_job = self.pipeline_jobs[modules][a_job_name]
                for index,one_a_job in enumerate(a_job):
                    makedir(one_a_job.Shell_dir)
                    self.define_jobs_pub(one_a_job)
                    self.relyon_status_mark(modules, one_a_job)

    def define_jobs_pub(self,a_job):
        if a_job.Depend == []: return a_job
        a_job_depend = []
        [a_job_depend.append(i.split(" ")[-1]) for i in a_job.Depend]
        for one_thisjob_depend in a_job_depend:
            target_path_list = get_dict_target.getpath(self.pipeline_jobs, one_thisjob_depend)
            if  target_path_list and len(target_path_list) >= 2:
                depend_job = self.pipeline_jobs[target_path_list[0]][target_path_list[1]]
                a_job.Depend.remove('{0}'.format(one_thisjob_depend))
                for one_depend_job in depend_job:
                    wait_add_depend = '{1.Name}'.format(a_job, one_depend_job)
                    if wait_add_depend not in a_job.Depend:
                        a_job.Depend.append(wait_add_depend)
            elif target_path_list and len(target_path_list) == 1:# main module depend define
                depend_module = self.pipeline_jobs[target_path_list[0]]
                a_job.Depend.remove('{0}'.format(target_path_list[0]))
                for childmodule in depend_module:
                    for one_depend_job in depend_module[childmodule]:
                        wait_add_depend = one_depend_job.Name
                        if wait_add_depend not in a_job.Depend:
                            a_job.Depend.append(wait_add_depend)
            else:
                # a_job.Depend.remove('order {0.Name} after {1}'.format(a_job, one_thisjob_depend))
                pass
        # return a_job

    def resolution_makefile_unfold(self, cmd_str):
        new_cmd_str, new_cmd_list = '', ['set -e', 'set -o']
        cmd_list = cmd_str.split(' &&\\\n')
        for cmd in cmd_list:
            if pat5.search(cmd):
                # print(cmd)
                # print(os.popen(cmd + ' -n').readlines())
                # print('aaaaaaaaaaa')
                tmp_list = os.popen(cmd + ' -n').readlines()
                tmp_list[-1] = tmp_list[-1].rstrip()
                tmp_str = "".join(tmp_list)
                #for l_index,_ in enumerate(tmp_list):
                #    tmp_list[l_index] = tmp_list[l_index].strip()
                new_cmd_list.append(tmp_str)
            else:
                new_cmd_list.append(cmd)
        new_cmd_str += ' &&\\\n'.join(new_cmd_list)
        return new_cmd_str

    def config_element_iteration(self, config, para, db):
        self.project_config = config
        make = 'make'
        for modules in self.modules_list:
            for count, a_job_name in enumerate(self.pipeline_jobs[modules]):
                a_job = self.pipeline_jobs[modules][a_job_name]
                a_job.Shell_dir = os.path.join(self.outdir, modules, a_job_name)
                # cmds = []
                # makedir(a_job.Shell_dir)
                # shell_name = os.path.join(a_job.Shell_dir, '{0}_{1}'.format(modules,a_job.Name))
                if a_job.Part == '':
                    a_job.Module = modules
                    eval_cmd = 'a_job.format_command()[1].format(para=para ,OUTDIR="{1.outdir}", BIN="{1.pipe_bindir}", MainModule="{0.Module}", ChildModule="{Child_Name}",db=db, make=make)'.format(a_job, self, Child_Name=a_job_name)
                    cmd = self.resolution_makefile_unfold(eval(eval_cmd))
                    # cmds.append(cmd)
                    a_job.Command = [cmd]
                    self.pipeline_jobs[modules][a_job_name] = [a_job]
                    # self.pipeline_jobs[modules][a_job_name][a_job.Name] = a_job
                else:
                    run_sample = config[a_job.Part]
                    # pre_job_count = 0

                    if len(run_sample) > 0:
                        for index, value in enumerate(sorted(run_sample)):
                            tmp_a_job = copy.copy(a_job)
                            tmp_a_job.Module = modules
                            # print(tmp_a_job.format_command()[1],'xxx')
                            eval_cmd = 'tmp_a_job.format_command()[1].format(para=para , Part=value ,OUTDIR="{1.outdir}", BIN="{1.pipe_bindir}", MainModule="{0.Module}", ChildModule="{Child_Name}",db=db, make=make)'.format(tmp_a_job, self, Child_Name=a_job_name)

                            cmd = self.resolution_makefile_unfold(eval(eval_cmd))
                            # if cmd not in cmds:
                            #     cmds.append(cmd)

                            tmp_a_job.Name += '_' + str(value[0])
                            tmp_a_job.Command = [cmd]
                            tmp_a_job.format_Part(value)
                            if index == 0:
                                self.pipeline_jobs[modules][a_job_name] = []

                            self.pipeline_jobs[modules][a_job_name].append(tmp_a_job)
                    else:
                        std.fatal('{} is empty\n'.format(config[a_job.part]), exit_code=1)
        # return jobs

    def write_Command_to_file(self):
        for modules in self.pipeline_jobs:
            for jobs in self.pipeline_jobs[modules]:
                one_job = self.pipeline_jobs[modules][jobs]

                for one_one_job in one_job:
                    self.write_object_job(modules, one_one_job)

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
                eachstart_job = self.pipeline_jobs[eachstart_path_list[0]][eachstart_path_list[1]]
                self.change_depend_status(eachstart_job)

    def change_depend_status(self,one_job):
        for one_one_job in one_job:
            self.change_depend_status_pub(one_one_job)

    def change_depend_status_pub(self,one_job):
        one_job_depend = []
        [one_job_depend.append(i.split(" ")[-1]) for i in one_job.Depend]
        for one_depend_job_name in one_job_depend:
            one_depend_job_name_path_list = get_dict_target.getpath(self.pipeline_jobs, one_depend_job_name)
            if len(one_depend_job_name_path_list) == 3:
                local_index = \
                self.pipeline_jobs[one_depend_job_name_path_list[0]][one_depend_job_name_path_list[1]][
                    one_depend_job_name_path_list[2]]
                iterm_depend_job = \
                    self.pipeline_jobs[one_depend_job_name_path_list[0]] \
                    [one_depend_job_name_path_list[1]] \
                    [local_index]
                iterm_depend_job.Status = 'done'
                self.change_depend_status_pub(iterm_depend_job)
            elif len(one_depend_job_name_path_list) == 2:
                iterm_depend_job = \
                    self.pipeline_jobs[one_depend_job_name_path_list[0]] \
                    [one_depend_job_name_path_list[1]]
                iterm_depend_job.Status = 'done'
                self.change_depend_status_pub(iterm_depend_job)

    def delivary_pipeline(self):
        std.info("该模块为任务投递模块，每一个投递子类需要继承并重写")


def Mount_new_disk(waiting_check_list):
    values = {}
    pass

def main():
    parser = argparse.ArgumentParser(description='', formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog='author:\t{0}\nmail:\t{1}\ndate:\t{2}\n'.format(__author__, __mail__,__date__))

    parser.add_argument('-b', '--bin', help='pipeline bindir',dest='bindir', required=True,)
    parser.add_argument('-c', '--config', help='project config',dest='config', required=True,nargs="+")
    parser.add_argument('-tc', '--toolconfig', help='tool config',dest='tonfig')
    parser.add_argument('-pro', '--project', help='analysis project id', dest='project',default='Test')
    parser.add_argument('-p', '--point', help='startpoint', dest='point',nargs="+")
    parser.add_argument('-t', '--template', help='template file', dest='template',required=True)
    parser.add_argument('-l', '--list', help='job list file', dest='joblist')
    parser.add_argument('-m', '--method', help='run job method using SJM', dest='method',default='singularity',choices=['sge-singularity-sjm','sge-docker-sjm','sge-normal-sjm', 'sge-docker-wdl', 'k8s-docker-argo'])
    parser.add_argument('-r', '--run', help='run analysis pipeline', dest='run',action='store_true')
    parser.add_argument('-o', '--outdir', help='analysis result outdir', dest='outdir',type=str)

    args = parser.parse_args()
    #parameter deal
    makedir(args.outdir)
    outdir = obtain_file_realpath(args.outdir)
    pipe_bindir = obtain_file_realpath(args.bindir)

    ## tool config read
    if not args.tonfig or not os.path.exists(args.tonfig):
        args.tonfig = os.path.join('bin_tool', 'config', 'tools_config.ini')
    GlobalPara.configfile = args.tonfig
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
        ReadJob = SJM_Job(job_file=args.template, parameter=project_para,outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method, project=args.project, tonfig=args.tonfig)
    elif "argo" in args.method:
        from Workflow.K8S_argo.argo_workflow import ARGO_workflow
        ReadJob = ARGO_workflow(job_file=args.template, parameter=project_para, outdir=outdir, pipe_bindir=pipe_bindir, sjm_method=args.method, project=args.project)
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
    ReadJob.write_jobs_to_DAG()
    # Mount the default unmounted path into the container, waiting develop
    Mount_new_disk(project_config['DB'])
    # create others file of running need
    ReadJob.create_other_shsh()
    ReadJob.delivary_pipeline(is_run=args.run)

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print(__doc__)
        sys.exit(1)

    main()
