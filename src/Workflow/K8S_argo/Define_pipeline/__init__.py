__slots__ = ('DAG','Job','Pipeline','Step','ags_dir')

import os
import re

from Workflow.K8S_argo.Define_pipeline.classification_define import DAG, Step, Job, Pipeline
from Workflow.version import tool_bin
from lib.public_method import myconf as Config, Log

std = Log(os.path.basename(__file__))

POD_NAME='${MY_POD_NAME}'
ags_config=Config()
ags_config.read('{}/config/tools_config.ini'.format(tool_bin))
__version__=ags_config['version']['version']
ags_dir=ags_config['software']['ags']
kubectl_dir=ags_config['software']['kubectl']
Pipeline.ags_dir=ags_dir
Pipeline.imagePullSecrets=re.split(';|\t',ags_config['image']['imagePullSecrets'])
Job.nodeSelector_key=ags_config['nodeSelector']['nodeSelector_key']
image_prefix=ags_config['image']['image_prefix']
Pipeline.start_finish_image=image_prefix+ags_config['image']['finish_image']
finish_sign=ags_config['sign']['finish_sign']

def fillResourceValue(value1,value2):
	assert value1 or value2,'resource should be defineded!'
	if not value1:value1=value2
	if not value2:value2=value1
	return value1,value2

def mem_format(mem):
	try:mem=float(mem)
	except ValueError as e:return mem
	return str(mem)+'Gi'

def config_format(para_config,inifile=None):
	config=Config()
	config.read('{}/config/tools_config.ini'.format(tool_bin))
	if inifile:config.read(inifile)
	for i in para_config:
		config[i].update(para_config[i])
	config={i:config[i] for i in config}
	job_config=dict(config['Job'])
	requests_cpu,limits_cpu=fillResourceValue(job_config['requests.cpu'],job_config['limits.cpu'])
	requests_mem,limits_mem=fillResourceValue(job_config['requests.memory'],job_config['limits.memory'])
	job_config['requests.cpu'],job_config['limits.cpu']=float(requests_cpu),float(limits_cpu)
	job_config['requests.memory'],job_config['limits.memory']=mem_format(requests_mem),mem_format(limits_mem)
	if job_config['maxtask']=='N' or int(job_config['maxtask'])>500:job_config['maxtask']=500#too many pods may Unsteadily
	else:job_config['maxtask']=int(job_config['maxtask'])
	assert job_config['maxtask']>0,'maxtask should not less than 1'
	if '/' not in job_config['image']:job_config['image']=image_prefix+job_config['image']
	job_config['work_dir']=os.path.abspath(job_config['work_dir'])
	config['Job']=job_config
	return config

def signJudge(infile):
	if os.path.isfile(infile):
		with open(infile) as f:
			sign=f.read().strip()
		if sign==finish_sign:
			return True
	return False

def ini2Job(config,ini_name):
	job_config=config['Job']
	work_dir=job_config['work_dir']
	para_dict=config['inputs.parameters']
	maxtask=job_config['maxtask']
	assert maxtask>0,'maxtask<1 is invalid'
	#TaskGroup={'name':job_config['name']+'-TaskGroup','steps':[]}
	job_template=Job(job_config['name'],para_list=['shell'])
	job_template.set_resource(job_config)
	job_template.set_workDir(work_dir)
	job_template.set_runCommand('sh {{inputs.parameters.shell}} 1>{{inputs.parameters.shell}}.o.%s 2>{{inputs.parameters.shell}}.e.%s'%(POD_NAME,POD_NAME))
	step=Step(job_template.name+'-'+'TaskGroup')
	n=0
	if len(config['shell'])<=100 or maxtask<=10:
		for shell_name in config['shell']:
			shell=config['shell'][shell_name].strip()
			if shell=='FINISH-STEP':
				step.next()
				step.add_task(shell_name,shell,{'FinishSign':finish_sign,'module_name':os.path.basename(ini_name),'ini_dir':os.path.dirname(ini_name)})
				continue
			for para in para_dict:
				shell=shell.replace('{{%s}}'%para,para_dict[para]).replace('{{inputs.parameters.%s}}'%para,para_dict[para])
			if n%maxtask==0:step.next()
			n+=1
			step.add_task(name=shell_name,template=job_template.name,para_dict={'shell':shell})
		if n==0:step.next()
	else:
		loop=[]
		for shell_name in config['shell']:
			shell=config['shell'][shell_name].strip()
			if shell=='FINISH-STEP':
				step.next()
				step.add_loop(template=job_template.name,a_para='shell',value_list=loop)
				loop=[]
				step.next()
				step.add_task(shell_name,shell,{'FinishSign':finish_sign,'module_name':os.path.basename(ini_name),'ini_dir':os.path.dirname(ini_name)})
				continue
			for para in para_dict:
				shell=shell.replace('{{%s}}'%para,para_dict[para]).replace('{{inputs.parameters.%s}}'%para,para_dict[para])
			loop.append(shell)
			n+=1
			if n%maxtask==0:
				step.next()
				step.add_loop(template=job_template.name,a_para='shell',value_list=loop)
				loop=[]
		if len(loop)>0:
			step.next()
			step.add_loop(template=job_template.name,a_para='shell',value_list=loop)
	entrypoint=step.name
	return entrypoint,[job_template,step]

def cmd2Job(config,cmd,stdout=None,stderr=None):
	job_config=config['Job']
	work_dir=job_config['work_dir']
	job_template=Job(job_config['name'],cmd,stdout=stdout,stderr=stderr,work_dir=work_dir)
	job_template.set_resource(job_config)
	return job_template.name,[job_template]

def shell2Job(config,shell,stdout=None,stderr=None):
	job_config=config['Job']
	work_dir=job_config['work_dir']
	job_template=Job(job_config['name'],'sh {}'.format(shell),stdout=stdout,stderr=stderr,work_dir=work_dir)
	job_template.set_resource(job_config)
	return job_template.name,[job_template]