#!/usr/local/bin/python3
# -*- coding: gbk -*-

import argparse
import copy
import os,re
import sys
import markdown

bin_tool = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(bin_tool,'lib'))
from lib.authority import Authorize, AuthorCode
from lib.QC_Result import *

std = Log(os.path.basename(__file__))

from Workflow.version import __author__, __date__, __mail__, tool_bin
from Workflow import (
    GlobalPara, 
    method2class
)

globalpara = GlobalPara()
"""
base method to create pipeline model
"""

def active_tool(actOBJ):
    regist_state = actOBJ.regist()
    if not regist_state:
        std.fatal("Activation failed!!!")

def main():

    ##################Permission verification##############
    author_handle = Authorize(toolbin=bin_tool + '/../')
    CheckStatus, residueday = author_handle.checkAuthored()
    if CheckStatus == AuthorCode.Author_right:
        pass
    elif CheckStatus == AuthorCode.Author_overtime:
        std.warning("Authorization timeout, please reactivate!!!")
        active_tool(author_handle)
    elif CheckStatus == AuthorCode.Author_NoneDecode:
        std.warning("Activation file information error!!!")
        active_tool(author_handle)
    elif CheckStatus == AuthorCode.Author_NoneRegist:
        std.warning("No active file")
        active_tool(author_handle)
    if int(residueday) <= 100 :print("residueday:", residueday, "days")
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
                        choices=list(method2class.keys()))
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
    ReadJob = method2class[args.method](job_file=args.template, parameter=project_para,
                                        outdir=outdir, pipe_bindir=pipe_bindir,
                                        sjm_method=args.method, project=args.project)

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
    mountCheckList=[]
    for key, value in project_config.items():
        mountCheckList = copy.copy(value)
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
