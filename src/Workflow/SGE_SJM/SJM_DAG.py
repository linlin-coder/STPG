from lib.public_method import *
from lib.public_method import *
from pipeline_generate import Parser_Job
from Workflow.version import tool_bin as bin_tool

class Deliver_DAG_Job():
    def __init__(self,job_file, parameter, outdir, pipe_bindir, sjm_method):
        self.Env = ''
        # self.location = 'fz'
        # self.sjm_method = sjm_method.split('-')[-1]
        # self.config = Config(os.path.join(bin_tool,'config','tools_config.ini'))
        # self.find_missin_location()
        # self.get_software_lib()

    def normal_qsub(self, software, mount_list, Image):
        env_one = 'sh'
        self.Env = env_one

    def get_software_lib(self,container_method):
        self.software = self.config.all_block('software', container_method)
        self.sjm = self.config.all_block('software', 'sjm')
        self.sjm_lib = 'LD_LIBRARY_PATH=' + self.config.all_block('lib', 'sjm')
        self.mount_list = self.config.all_block('mount', 'mount').split("|")
        self.sge_root = self.config.all_block('lib', 'sge_root')

    def public_qsub(self, Image):
        container_method = self.sjm_method.split('-')[-2]
        self.config = Config(self.tonfig)
        self.get_software_lib(container_method)
        if Image:
            eval_cmd = 'self.{0}_qsub("{1}",{2}, "{3}")'.format(container_method,self.software,self.mount_list, Image)
            eval(eval_cmd)
        else:
            self.normal_qsub(self.software, self.mount_list, Image)


    def docker_qsub(self, software, mount_list, Image):
        mount_str = ' -v '.join(mount_list)
        env_one = '%s run --rm --user $(id -u ${USER}):$(id -g ${USER})  -v %s %s /bin/bash ' % (software, mount_str, Image)
        self.Env = env_one

    def singularity_qsub(self, software, mount_list, Image):
        mount_str = ' -B '.join(mount_list)
        env_one = '{0} run --cleanenv -B {1} {2} /bin/bash '.format(software, mount_str, Image)
        self.Env = env_one

    def find_missin_location(self):
        local_ip = subprocess_run("env| grep SSH_CONNECTION| awk '{print $(NF-1)}'").strip()
        local_dict = self.config.return_block_list("mark")
        for ip_local, value in local_dict.items():
            if local_ip in value:
                self.location = ip_local.split('_')[-1]
                break

class SJM_Job(Parser_Job,Deliver_DAG_Job):
    def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project, tonfig):
        self.job_file = job_file
        # self.project_configdir = args.config
        self.para = parameter
        self.job_list = ""  # this define job list file,and write on one raw
        self.pipe_bindir = pipe_bindir
        self.project = project
        self.outdir = outdir
        self.tonfig = tonfig
        self.sjm_method = sjm_method
        # self.pipeline_jobs_dict = multidict()
        super(SJM_Job,self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)
        # super(SJM_Job,self).__init__(sjm_method)

    def write_jobs_to_DAG(self,):
        makedir(os.path.join(self.outdir,'log'))
        DAG_outfile = os.path.join(self.outdir,'log','Analysis.job')
        job_content = ''; order_content = ''
        with open(DAG_outfile, 'w') as fout:
            for modules in self.modules_list:
                for count, a_job_name in enumerate(self.pipeline_jobs[modules]):
                    a_job = self.pipeline_jobs[modules][a_job_name]
                    # if isinstance(a_job, list):
                    for index,one_a_job in enumerate(a_job):
                        # one_a_job = self.define_jobs_pub(one_a_job)
                        # self.pipeline_jobs[modules][a_job_name][index] = one_a_job
                        job_content, order_content = self.define_sjm_one_job(one_a_job,job_content, order_content)

            fout.write(job_content + "\n" + order_content)

    def define_sjm_one_job(self, one_job, job_content = '', order_content = ''):
        self.public_qsub(one_job.Image)

        job_content += '\njob_begin'
        job_content += '\n\tname {0.Name}\n\tstatus {0.Status}\n\tsched_options -V -cwd -l vf={0.Memory},p={0.CPU} -q {0.Queue}\n\tcmd {1.Env} {0.Shell_dir}/{0.Module}-{0.Name}.sh\n'.format(one_job, self)
        job_content += 'job_end'

        for one_depend in one_job.Depend:
            order_content += 'order {0.Name} after {1}\n'.format(one_job, one_depend)

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
        if hasattr(self.default, "Image") and self.default.Image:
            self.public_qsub(self.default.Image)

        self.sh_sjm_Analysis = os.path.join(self.outdir,'sjm_Analysis.sh')
        with open(self.sh_sjm_Analysis, 'w') as f_sjm:
            f_sjm.write('cd {0.outdir}/log && export SGE_ROOT={0.sge_root} && export {0.sjm_lib} && {0.sjm} -i -l Analysis.job.status.log Analysis.job\n'.format(self))

        environment = os.path.join(self.outdir, 'sh_Docker_environment.sh')
        if self.sjm_method != 'normal':
            with open(environment, 'w') as f_env:
                f_env.write(self.Env.replace('--rm','--rm -it') + ' `readlink -f $1`')#.replace('/bin/bash','').replace('singularity run','singularity shell')

        environment = os.path.join(self.outdir, 'entry_Docker_environment.sh')
        if self.sjm_method != 'normal':
            with open(environment, 'w') as f_env:
                if self.sjm_method != 'singularity':
                    f_env.write(self.Env.replace('--rm', '--rm -it').replace('/bin/bash', '').replace('singularity run','singularity shell'))
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
                std.fatal('sjm-job投递失败', exit_code=p.poll())
            else:
                std.info("sjm-job 开始投递，任务日志为{0}，请注意观察任务状态".format(os.path.dirname(self.sh_sjm_Analysis)+'/log/*log'))
            if guard:
                # while 1:
                #     pass
                pass
