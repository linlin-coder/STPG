import collections
import os
import subprocess
import sys
import time

import yaml

import Workflow
import lib.public_method
from Workflow.K8S_argo.Define_pipeline import *
from Workflow.version import __version__
from lib.public_method import myconf as Config
from Workflow.BaseParserJob.baseworkflow import Parser_Job

bindir=os.path.dirname(os.path.realpath(__file__))
std.filename = os.path.basename(__file__)

class ARGO_workflow(Parser_Job):
	def __init__(self, job_file, parameter, outdir, pipe_bindir, sjm_method, project):
		self.job_file = job_file
		# self.project_configdir = args.config
		self.para = parameter
		self.mount_list = []
		self.job_list = ""  # this define job list file,and write on one raw
		self.pipe_bindir = pipe_bindir
		self.outdir = outdir
		self.project = project
		self.sjm_method = sjm_method
		self.yaml_file = os.path.join(self.outdir,'{}.yaml'.format(project))
		self.dependence_file = os.path.join(self.outdir,'{}.dependence.ini'.format(project))
		# self.pipeline_jobs_dict = multidict()
		super(ARGO_workflow, self).__init__(job_file, parameter, outdir, pipe_bindir, sjm_method)

	def ascertain_data_mount(self):
		volume_for_mount = Job('tmp').volumeMounts
		volume_for_mount_dict = {volume_for_mount[i]['mountPath']: volume_for_mount[i]['name'] for i in volume_for_mount}

		volumeMounts_ = set()
		values = {self.pipe_bindir, self.outdir}
		for config_part in self.project_config:
			for line in self.project_config[config_part]:
				if config_part in ['Para', 'DB']:
					values.update(line[0].strip().split('=')[1:])
				else:
					values.update(line)
		for value in values:
			if not value or not value.startswith('/'): continue
			path = os.path.realpath(value)
			"""根目录为第一层，固定只检查前三层路径，后续有变动再修改"""
			prefix_path = '/'.join(path.split('/', 3)[:3])
			if prefix_path in volume_for_mount_dict:
				volumeMounts_.add(volume_for_mount_dict[prefix_path])
		default_job_config = Config()
		default_job_config.read('{}/job_default.ini'.format(bindir))
		# pr
		volumeMounts = [i.strip() for i in default_job_config['Job']['volumeMounts'].split(';')]
		"""无论如何配置config，都要挂载本地路径"""
		if 'nas' not in volumeMounts_:
			if 'nas' in volumeMounts_: volumeMounts_.remove('nas')  ##逻辑有点奇怪。。。。
		else:
			pass
		# del default_job_config, volumeMounts_
		del volumeMounts_
		std.info('path: {}'.format(' '.join(volumeMounts)))

		return default_job_config, volumeMounts

	def DAG2yaml(self, dependencies, shell_dir, jobname, pub_config={'Job':{}},  restart=1):
		"""

		@param dependencies: 从get_dependence 函数返回的结果，job依赖的dict
		"""
		pipeline = Pipeline(jobname)
		pipeline.set_parameters({'OUTDIR':self.outdir, 'bindir':self.pipe_bindir})
		dag = DAG(jobname + '-dag')
		for modules in self.pipeline_jobs:
			for jobs in self.pipeline_jobs[modules]:
				module_inifile = os.path.join(shell_dir, modules, jobs.replace('_','-') + '.ini')
				if not os.path.isfile(module_inifile):
					std.fatal('can not find {}'.format(module_inifile), exit_code=1)
				config = config_format(pub_config, module_inifile)
				module_bool_success = signJudge(os.path.join(shell_dir, modules, jobs + '.sign'))
				if module_bool_success and restart in [1, 2]:
					std.warning('Module {} has finished, so skip'.format(modules + '/' + jobs))
					config['shell'] = {}
				for shell_name in list(config['shell'].keys()):
					shell = os.path.join(config['Job']['work_dir'], config['shell'][shell_name])
					shell_bool_success = signJudge(os.path.join(shell + '.sign'))
					if shell_bool_success and restart == 2:
						std.warning('Task {}/{} has finished, so skip'.format(modules+jobs, shell_name))
						del config['shell'][shell_name]

				entrypoint, templates = ini2Job(config, os.path.join(shell_dir, modules, jobs))
				pipeline.add_template(templates)
				for a_job in self.pipeline_jobs[modules][jobs]:
					dag.add_dependence(a_job.Module+'-'+a_job.JName.replace('_','-'), dependencies[a_job.Module+'-'+a_job.JName.replace('_','-')], entrypoint)
		pipeline.add_start_finish_template()
		pipeline.add_template([dag])
		pipeline.set_entrypoint(dag.name)
		# if args.ttl: pipeline.set_ttlSecond(args.ttl)
		yaml.dump(dict(pipeline), open(self.yaml_file, 'w'))

	def write_jobs_to_DAG(self):
		pass

	def _cleanup(self):
		alltask = self.pipelineGraph.getVertices()
		for oneTask in alltask:
			lib.public_method.subprocess_run('rm -f {0}*.sh*'.format(os.path.join(oneTask.Shell_dir, oneTask.Module)))
			lib.public_method.subprocess_run('rm -f {0}/*/*.{{ini,sign}}'.format(self.outdir))

	def delivary_pipeline(self, is_run=True, guard=True):
		log_file = os.path.join(self.outdir,'log.txt')
		cmd = ' '.join([ags_dir, 'submit', self.yaml_file, '-n argo'])
		if is_run:
			p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			submit_log = [i.decode() for i in p.stdout]
			sys.stdout.write(''.join(submit_log))
			if p.wait() != 0:
				std.fatal('yaml投递失败', exit_code=p.poll())
			WorkflowID = ''
			for line in submit_log:
				line_tmp = line.strip().split(':')
				if len(line_tmp) >= 2 and line_tmp[0].strip() == 'Name':
					WorkflowID = line_tmp[1].strip()
			if not WorkflowID:
				std.error('unknown WorkflowID')
			with open(log_file, 'a') as f:
				f.write('#WorkflowID: {}\n'.format(WorkflowID))
			if guard:
				while 1:
					get_cmd = ' '.join([ags_dir, 'get', WorkflowID, '-n argo'])
					get_p = subprocess.Popen(get_cmd, stdout=subprocess.PIPE, shell=True)
					status = None
					for line in get_p.stdout:
						line = line.decode()
						line_tmp = line.strip().split(':')
						if len(line_tmp) >= 2 and line_tmp[0].strip() == 'Status':
							status = line_tmp[1].strip()
							break
					if status in ['Pending', 'Running']:
						pass
					elif status == 'Failed':
						std.error('Workflow: {} running failed'.format(WorkflowID))
						exit_status = 1
						break
					elif status == 'Succeeded':
						std.info('Workflow: {} running success'.format(WorkflowID))
						exit_status = 0
						break
					else:
						std.error('Workflow: {} unknown status, {}'.format(WorkflowID, status))
						exit_status = 2
						break
					get_p.wait()
					time.sleep(10)
				self._cleanup()
				sys.exit(exit_status)

	def write_Command_to_file(self):
		# volumeMounts = self.ascertain_data_mount()
		self.get_dependence()
		# shell_dir = '.'
		shell_name_dict = collections.OrderedDict()
		all_task_list = self.pipelineGraph.getVertices()
		JNameTasks = {}
		for one_one_job in all_task_list:
			self.supplement_element(one_one_job)
			self.write_object_job(one_one_job.Module, one_one_job)
			shell_basename = '{0}-{1}'.format(one_one_job.Module, one_one_job.Name)
			shsh = os.path.join(one_one_job.Shell_dir, shell_basename) + '.sh'
			shell_name_dict[shell_basename] = shell_basename + '.sh'
			with open(shsh, 'w') as f:
				f.write('\n'.join(one_one_job.Command))
			DecorateJName = one_one_job.JName.replace('_','-')
			if DecorateJName not in JNameTasks:
				JNameTasks[DecorateJName] = {}
				JNameTasks[DecorateJName]['shell'] = {}
			JNameTasks[DecorateJName]['shell'][shell_basename] = shell_basename + '.sh'
			JNameTasks[DecorateJName]['Module'] = one_one_job.Module
			JNameTasks[DecorateJName]['OneTask'] = one_one_job

		for JName,Task_dict in JNameTasks.items():
			shell_name_dict = Task_dict['shell']
			shell_name_dict['{}-Finish'.format(JName)] = 'FINISH-STEP'
			inifile = os.path.join(self.outdir, Task_dict['Module'], JName + '.ini')
			dump2JobINI(inifile, JName, Task_dict['OneTask'], shell_name_dict)
		self.DAG2yaml(self.dependence_dict, shell_dir=self.outdir, jobname=self.project, )

	def supplement_element(self, a_job):
		default_job_config, volumeMounts = self.ascertain_data_mount()
		# for modules in self.pipeline_jobs:
		# 	# if order<=0:continue
		# 	for child_job in self.pipeline_jobs[modules]:
		# 		# print(modules, child_job, self.pipeline_jobs[modules], self.pipeline_jobs)
		# 		for a_job in self.pipeline_jobs[modules][child_job]:
		# 			# setattr(a_job, 'Env', args.Env)
		setattr(a_job, 'MaxTask', default_job_config['Job']['maxtask'])
		setattr(a_job, 'LimitCPU', default_job_config['Job']['limits.cpu'])
		setattr(a_job, 'LimitT', default_job_config['Job']['limit.fold'])
		setattr(a_job, 'Retry', default_job_config['Job']['retrytimes'])
		setattr(a_job, 'volumeMounts', volumeMounts)
	# @
	def get_dependence(self, ):
		self.dependence_dict=collections.OrderedDict()
		module_dict={}
		if len(self.pipeline_jobs)>0:
			# start_order=sorted(jobs)[0]
			# order_tmp=0
			all_task_list = self.pipelineGraph.getVertices()
			for a_job in all_task_list:
				module_dict[a_job.Name]=a_job.Name
				if a_job.Depend in ([],['']) :#and order!=start_order:
					#dependecies_tmp=[jobs[order_tmp][0].Name]
					dependecies_tmp=[]#{i.Name for i in jobs[order_tmp]}
				else:
					dependecies_tmp=set(a_job.Depend)
				dependecies=[]
				dependeciesTasks = self.pipelineGraph.getVertex(a_job).prefix
				'''for dependece in dependecies_tmp:
					if dependece not in module_dict:
						std.fatal('can not find depend module {} before module {}'.format(dependece,a_job.Name),exit_code=1)
					dependecies.append(module_dict[dependece])'''
				self.dependence_dict[a_job.Module+'-'+a_job.JName.replace('_','-')]=list(set([task.id.Module+'-'+task.id.JName.replace('_','-') for task in dependeciesTasks]))
		print(self.dependence_dict)# order_tmp=order
		# return dependence_dict,module_dict

	def create_other_shsh(self):
		pass

def dump2JobINI(inifile,job_group_name, a_job,shell_name_dict):
	# print('aa',a_job.__dict__)
	job_config=Config()
	job_config.add_section('INI_info')
	job_config.set('INI_info','version',__version__)

	job_config.add_section('inputs.parameters')
	#job_config.set('inputs.parameters','shell_dir',os.path.join(shell_dir,a_job.indexJobName))

	job_config.add_section('Job')
	job_config.set('Job','name',job_group_name)
	if getattr(a_job,'CPU',None):
		job_config.set('Job','limits.cpu',str('%.1f' %(float(a_job.CPU)*float(a_job.LimitCPU))))
		job_config.set('Job','requests.cpu',str(a_job.CPU))
	if getattr(a_job,'Memory',None):
		a_job.Memory = a_job.Memory.replace('G','')
		job_config.set('Job','limits.memory',str('%.1f' %(float(a_job.Memory)*float(a_job.LimitT)))+'Gi')
		job_config.set('Job','requests.memory',a_job.Memory+'Gi')
	if getattr(a_job,'Image',None):
		job_config.set('Job','image',a_job.Image)
	if getattr(a_job,'Env',None):
		job_config.set('Job','nodeSelector','\t'.join(a_job.Env))
	#if getattr(a_job,'Hostname',None):
	#	job_config.set('Job','hostname',a_job.Hostname)
	if getattr(a_job,'Retry',None):
		job_config.set('Job','retrytimes',a_job.Retry)
	if getattr(a_job,'MaxTask',None):
		job_config.set('Job','maxtask',a_job.MaxTask)
	if getattr(a_job,'Shell_dir',None):
		job_config.set('Job','work_dir',a_job.Shell_dir)
	if getattr(a_job,'volumeMounts',None) :
		job_config.set('Job','volumeMounts','\t'.join(a_job.volumeMounts))

	default_job_config=Config()
	default_job_config.read('{}/job_default.ini'.format(bindir))
	for i in default_job_config['Job']:
		if i not in job_config['Job']:
			job_config.set('Job','#{}'.format(i),default_job_config['Job'][i])

	job_config.add_section('shell')
	for i in shell_name_dict:
		shellname = i.replace('_','-')
		shell=shell_name_dict[i]
		job_config.set('shell',shellname,shell)
	#if len(shell_name_dict)>0:job_config.set('shell','{}-Finish'.format(a_job.Name),'FINISH-STEP')
	with open(inifile,'w') as fout:
		job_config.write(fout)
		fout.write("""#JobINI说明：
#1、[shell]内可用{{xxx}}表示变量，{{workflow.parameters.xxx}}为全局变量，其余为局部变量，表示的时候不要有空格
#2、FINISH-STEP为[shell]的保留关键字，作用是为当前JOB的产生结束标志，可选择不加
#3、memory默认单位为Gi
""")
		if getattr(a_job,'Description',None):
			fout.write('\n#模块说明：\n#{}\n'.format(a_job.Description))


