import json
from jinja2 import PackageLoader, Environment, FileSystemLoader

from Workflow.version import tool_bin
from lib.public_method import *
from Workflow.BaseParserJob.baseworkflow import Parser_Job

bindir = os.path.realpath(os.path.dirname(__file__))

__name__ = 'WDL_Workflow'
'''
将模板命令解析为WDL可以运行的任务，包含如下：
按module划分，将任务写入到不同的task中，暂时不支持任务并行（不同看起来稍加修改，应该能实现并行）
任务依赖写在task的output中，为一个string类型
'''

class WDL_Workflow(Parser_Job):
    Name = "WDL_Workflow"
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project):
        super(WDL_Workflow,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)
        self.env = Environment(loader=FileSystemLoader(os.path.join(bindir, 'template')))
        self.pipeline_outdir = self.outdir
        self.project = project
        # self.tonfig = tonfig
        # self.config = Config(tonfig)

    def write_children_taskwdl(self):
        """
        把同一个children_module 的所有task写入到一个task.wdl中，且文件夹名为parent_module名称
        pipeline的关系如下：
        parent_module:
            - children_module
                - task1
                    - Command
                    - Depend
                    - Name
                - task2
                - task3
        """
        for modules in self.pipeline_jobs:
            for jobs in self.pipeline_jobs[modules]:
                one_job = self.pipeline_jobs[modules][jobs]
                jinja2_render = self.env.get_template(os.path.join('subtask.wdl')).render(children_jobs=one_job, pipelineGraph=self.pipelineGraph).replace('{|','{')
                subtask_file = os.path.join(self.pipeline_outdir,'module',modules,jobs+'.task.wdl')
                makedir(os.path.dirname(subtask_file))
                with open(subtask_file, 'w') as fo:fo.write(jinja2_render)

    def write_pipeline_workflow(self):
        jinja2_render = self.env.get_template(os.path.join('pipeline.workflow.wdl')).render(pipeline_jobs=self.pipeline_jobs, pipelineGraph=self.pipelineGraph)
        self.pipeline_file = os.path.join(self.pipeline_outdir, 'module', 'pipeline.workflow.wdl')
        with open(self.pipeline_file, 'w') as fo: fo.write(jinja2_render)
        # 拷贝公共函数wdl文件
        copy_target_dir(os.path.join(bindir,'template', 'common'), os.path.join(self.outdir,'module','common'))

    def delivary_pipeline(self, is_run=False):
        # return WDL_cmd
        if is_run:
            p = subprocess.Popen(self.WDL_cmd, shell=True,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            submit_log = [i.decode() for i in p.stdout]
            sys.stdout.write(''.join(submit_log))
            if p.wait() != 0:
                std.fatal('WDL-pipeline 投递失败', exit_code=p.poll())

    # def write_Command_to_file(self):
    #     pass

    def write_jobs_to_DAG(self):
        self.write_children_taskwdl()
        self.write_pipeline_workflow()

    def rewrite_input_josn(self):
        input_template = os.path.join(tool_bin, 'Workflow/Cromwell/template/input.json')
        with open(input_template, 'r') as f_input:
            input_content = json.load(f_input)
        # input_content["pipeline.outdir"] = self.pipeline_outdir
        input_content["pipeline.config_json"] = os.path.join(tool_bin, 'Workflow/Cromwell/template/config.json')
        project_input = os.path.join(self.pipeline_outdir,'input.json')
        with open(project_input, 'w') as f_input:
            json.dump(input_content, f_input, indent=2)
        return project_input

    def create_other_shsh(self):
        java = self.globalMSG.software.java
        cromwell = self.globalMSG.software.Cromwell
        HPC_conf = self.globalMSG.path.WDLBeckendConf
        input_json = self.rewrite_input_josn()
        self.WDL_cmd = f'''{java} -Dconfig.file={HPC_conf} -jar {cromwell} run {self.pipeline_file} -i {input_json}'''
        shsh = os.path.join(self.pipeline_outdir, self.project + '_wdl_run.sh')
        with open(shsh, 'w') as fo:fo.write(self.WDL_cmd)

