# from lib.public_method import *
from lib.public_method import *
from Workflow.BaseParserJob.baseworkflow import Parser_Job
from Workflow.version import tool_bin as bin_tool

class Deliver_DAG_Job():
    def __init__(self,job_file, parameter, outdir, pipe_bindir, sjm_method):
        self.Env = ''
        # self.config = Config(self.tonfig)
        # container_method = self.sjm_method.split('-')[-2]
        # self.get_software_lib(container_method)

    def normal_qsub(self, Image):
        env_one = 'sh'
        self.Env = env_one

    def DefineDefault(self) -> None:
        container_method = self.sjm_method.split('-')[-2]
        self.get_software_lib(container_method)

    def judge_dir_exist(self, config_mount):
        for onemount in config_mount:
            outdir = onemount.split(":")[0]
            if 1:#obtain_file_realpath(outdir):
                test_mount = '/'.join(outdir.split("/")[:3]) + ":" + '/'.join(outdir.split("/")[:3]) + ":ro"
                if test_mount not in self.mount_list:
                    self.mount_list.append(onemount)
                elif len(onemount.split(":")) < 3 or onemount.split(":")[-1] != 'ro':
                    self.mount_list.remove(test_mount)
                    self.mount_list.append(onemount)

    def get_software_lib(self,container_method):
        self.sjm = self.globalMSG.software.sjm
        self.sge_root = self.globalMSG.path.SGERoot

    def public_qsub(self, Image, mount_list):
        container_method = self.sjm_method.split('-')[-2]
        self.judge_dir_exist(mount_list)
        if Image:
            eval_cmd = 'self.{0}_qsub("{1}")'.format(container_method, Image)
            eval(eval_cmd)
        else:
            self.normal_qsub(self.software, self.mount_list, Image)


    def docker_qsub(self, Image):
        mount_str = ' -v '.join(self.mount_list)
        env_one = '%s run --rm --user $(id -u ${USER}):$(id -g ${USER})  -v %s %s /bin/bash ' % (self.globalMSG.software.docker, mount_str, Image)
        self.Env = env_one

    def singularity_qsub(self, Image):
        mount_str = ' -B '.join(self.mount_list)
        env_one = '{0} exec --cleanenv -B {1} {2} /bin/bash '.format(self.globalMSG.software.singularity, mount_str, Image)
        self.Env = env_one

    def find_missin_location(self):
        local_ip = subprocess_run("env| grep SSH_CONNECTION| awk '{print $(NF-1)}'").strip()
        local_dict = self.config.return_block_list("mark")
        for ip_local, value in local_dict.items():
            if local_ip in value:
                self.location = ip_local.split('_')[-1]
                break

class SJM_Job(Parser_Job,Deliver_DAG_Job):
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
        # self.pipeline_jobs_dict = multidict()
        super(SJM_Job,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)
        # super(SJM_Job,self).__init__(sjm_method)

    def write_jobs_to_DAG(self,):
        self.DefineDefault()
        makedir(os.path.join(self.outdir,'log'))
        DAG_outfile = os.path.join(self.outdir,'log','Analysis.job')
        job_content = ''; order_content = ''
        all_task_list = self.pipelineGraph.getVertices()
        with open(DAG_outfile, 'w') as fout:
            for one_a_job in all_task_list:
                job_content, order_content = self.define_sjm_one_job(one_a_job,job_content, order_content)

            fout.write(job_content + "\n" + order_content)

    def define_sjm_one_job(self, one_job, job_content = '', order_content = ''):
        self.mount_list = []
        self.public_qsub(one_job.Image, one_job.Mount)

        job_content += '\njob_begin'
        job_content += '\n\tname {0.Name}\n\tstatus {0.Status}\n\tsched_options -V -cwd -l vf={0.Memory},p={0.CPU} -q {0.Queue}\n\tcmd {1.Env} {0.Shell_dir}/{0.Module}-{0.Name}.sh\n'.format(one_job, self)
        job_content += 'job_end'
        for one_depend in self.pipelineGraph.getVertex(one_job).getConnections():
            order_content += 'order {1.Name} after {0.Name}\n'.format(one_job, one_depend.id)

        return job_content, order_content


    def write_Command_to_file(self):
        for modules in self.pipeline_jobs:
            for jobs in self.pipeline_jobs[modules]:
                one_job = self.pipeline_jobs[modules][jobs]

                # if isinstance(one_job, list):
                for one_one_job in one_job:
                    self.write_object_job(modules, one_one_job)

    def write_object_job(self,modules, one_job):
        shell_basename = '{0}-{1}'.format(modules, one_job.Name)
        shsh = os.path.join(one_job.Shell_dir, shell_basename) + '.sh'
        with open(shsh, 'w') as f:
            f.write('\n'.join(one_job.Command))

    def create_other_shsh(self):
        # 把default中的attr提供给ENV
        self.mount_list = []
        if hasattr(self.default, "Image") and self.default.Image:
            self.public_qsub(self.default.Image, self.default.Mount)

        self.sh_sjm_Analysis = os.path.join(self.outdir,'sjm_Analysis.sh')
        with open(self.sh_sjm_Analysis, 'w') as f_sjm:
            f_sjm.write('cd {0.outdir}/log && export SGE_ROOT={0.sge_root} && {0.sjm} -i -l Analysis.job.status.log Analysis.job\n'.format(self))

        environment = os.path.join(self.outdir, 'sh_Docker_environment.sh')
        if self.sjm_method != 'normal':
            with open(environment, 'w') as f_env:
                f_env.write(self.Env.replace('--rm','--rm -it') + ' `readlink -f $1`')#.replace('/bin/bash','').replace('singularity run','singularity shell')

        environment = os.path.join(self.outdir, 'entry_Docker_environment.sh')
        if self.sjm_method != 'normal':
            with open(environment, 'w') as f_env:
                if self.sjm_method != 'singularity':
                    f_env.write(self.Env.replace('--rm', '--rm -it').replace('/bin/bash', '').replace('singularity exec','singularity shell'))
                else:
                    f_env.write(self.Env.replace('--rm', '--rm -it').replace('/bin/bash', ''))

    def get_jobs_mainbody(self):
        pass

    def rewrite_file(self, job_tmp_dict, order_list, rewrite_file):
        rewrite_target = ["name", 'sched_options', "status", "cmd"]
        with open(rewrite_file,'w') as fi:
            # for job_name, job_dict in job_tmp_dict.keys():
            #     fi.write('job_begin')
            #     for key, value in job_dict.keys():
            #         pass
            for job_name, job_dict in job_tmp_dict.items():
                fi.write('job_begin\n')
                for rewrite in rewrite_target:
                    fi.write('\t{0}'.format(rewrite) + " " + job_dict[rewrite] + '\n')
                fi.write('job_end\n')

            for order in order_list:
                fi.write(order+'\n')

    def delivary_pipeline(self, is_run=True, log_file='', guard=True):
        cmd = ['/bin/bash', self.sh_sjm_Analysis]
        if is_run:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            submit_log = [i.decode() for i in p.stdout]
            sys.stdout.write(''.join(submit_log))
            if p.wait() != 0:
                # std.fatal('SJM job delivery failed!!!', exit_code=p.poll())
                std.warning('SJM job delivery failed!!!\t{exit_code}'.format(exit_code=p.poll()))
            else:
                std.info("SJM job starts delivery and the task log is {0}. Please observe the task status".format(os.path.dirname(self.sh_sjm_Analysis)+'/log/*log'))
            if guard:
                # while 1:
                #     pass
                pass
