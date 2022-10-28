import os
import re
import subprocess
import yaml

from Workflow.version import tool_bin
from lib.public_method import myconf as Config

ags_config=Config()
ags_config.read('{}/config/tools_config.ini'.format(tool_bin))
ags_dir=ags_config['software']['ags']
bindir = os.path.dirname(os.path.realpath(__file__))

class Job(dict):
	"""from Workflow.__init__"""
	nodeSelector_key=None
	# locale=''
	def __init__(self,name,cmd='',stdout=None,stderr=None,work_dir='./',para_list=[]):
		dict.__init__(self)
		self.name=name
		self.volumeMounts={}
		self._generate_JobTemplate()
		self.set_name(name)
		if stdout:cmd+=' 1>{}'.format(stdout)
		if stderr:cmd+=' 2>{}'.format(stderr)
		self.set_runCommand(cmd)
		self.set_workDir(os.path.realpath(work_dir))
		for i in para_list:
			self.add_inputs_para(i)
	def _generate_JobTemplate(self):
		self.update(yaml.load(open('{}/../template/Job_YamlTemplate.yaml'.format(bindir)),Loader=yaml.FullLoader))
		self.volumeMounts={i['name']:i for i in yaml.load(open('{}/../template/VolumeMounts_YamlTemplate.yaml'.format(bindir)),Loader=yaml.FullLoader)}
		self['container']['volumeMounts'].append(self.volumeMounts['timezone'])
		del self.volumeMounts['timezone']
		#self['container']['volumeMounts']+=volumeMounts
	def add_inputs_para(self,var_name):
		self['inputs']['parameters'].append({'name':var_name})
	def add_volumeMount(self,name):
		assert name in self.volumeMounts,'{} not a valid volumeMounts'.format(name)
		self['container']['volumeMounts'].append(self.volumeMounts[name])
	def set_workDir(self,work_dir):
		self['container']['workingDir']=work_dir
	def set_nodeSelector(self,key,value):
		#if key=="network" and value=="internet": #by renxue  还有可能贴其他标签
		self["tolerations"].append({"key":key,"value":value,"operator":"Equal","effect":"NoSchedule"})
		self['nodeSelector'][key]=value
	def set_resource(self,config_dict):
		for i in re.split('\t|;',config_dict['nodeSelector'].strip()):
			key, value = '', ''
			i=i.strip()
			i=i.split(':',1)
			if len(i)==0:continue
			elif len(i)==1:
				key=self.nodeSelector_key.strip()
				value=i[0].strip()
				if not value:continue
			elif len(i)==2:
				key,value=i[0].strip(),i[1].strip()
			self.set_nodeSelector(key,value)
		for i in re.split('\t|;',config_dict['volumeMounts'].strip()):
			i=i.strip()
			if i:self.add_volumeMount(i)
		self['container']['image']=config_dict['image']
		self['container']['resources']['requests']={'memory':config_dict['requests.memory'],'cpu':config_dict['requests.cpu']}
		self['container']['resources']['limits']={'memory':config_dict['limits.memory'],'cpu':config_dict['limits.cpu']}
		if int(config_dict['retrytimes'])>0:
			self['retryStrategy']={}
			self['retryStrategy']['limit']=int(config_dict['retrytimes'])
		if config_dict['hostname']:self['nodeSelector']['hostname']=config_dict['hostname']
	def set_entryCommand(self,command_list):
		self['container']['command']=command_list
	def set_runCommand(self,command):
		self['container']['args']=[command]
	def set_name(self,name):
		self.name=name
		self['name']=name

class Pipeline(dict):
	'''from Workflow.__init__'''
	ags_dir = ags_dir
	imagePullSecrets=[]
	start_finish_image=None
	# locale=''
	def __init__(self,name,work_dir='./'):
		dict.__init__(self)
		self.name=name
		self.volumeMounts_dict={}
		self._generate_PipelineTemplate()
		self.set_name(name)
		#self.finish_template_name=None
	def _generate_PipelineTemplate(self):
		self.update(yaml.load(open('{}/../template/Pipeline_YamlTemplate.yaml'.format(bindir)),Loader=yaml.FullLoader))
		volumes=yaml.load(open('{}/../template/Volume_YamlTemplate.yaml'.format(bindir)),Loader=yaml.FullLoader)
		self['spec']['volumes']+=volumes
		for imagePullSecret in self.imagePullSecrets:
			self['spec']['imagePullSecrets'].append({'name':imagePullSecret})
	def add_template(self,template_list=[]):
		for template in template_list:
			self['spec']['templates'].append(dict(template))
			for volumeMount in template.get('container',{}).get('volumeMounts',{}):
				if 'name' in volumeMount:
					self.volumeMounts_dict[volumeMount['name']]=dict(volumeMount)
	def add_start_finish_template(self):
		"""this function should be used after all templated added!!!"""
		assert self.start_finish_image,'err finish image'
		finish_template=yaml.load(open('{}/../template/FINISH-STEP_YamlTemplate.yaml'.format(bindir)),Loader=yaml.FullLoader)
		finish_template['container']['volumeMounts']+=list(self.volumeMounts_dict.values())
		finish_template['container']['image']=self.start_finish_image
		self['spec']['templates'].append(finish_template)
	def set_name(self,name):
		self['metadata']['generateName']=name+'-'
		self.name=name
	def set_entrypoint(self,entrypoint):
		self['spec']['entrypoint']=entrypoint
	def set_parameters(self,para_dict):
		for key in para_dict:
			self['spec']['arguments']['parameters'].append({'name':key,'value':para_dict[key]})
	def set_ttlSecond(self,ttlsecond):
		self['spec']['ttlSecondsAfterFinished']=ttlsecond
	def submit(self,ags_dir=None):
		if not ags_dir:ags_dir=self.ags_dir
		p=subprocess.Popen([ags_dir,'submit','-'],stdin=subprocess.PIPE)
		p.stdin.write(yaml.dump(dict(self)).encode())
		p.stdin.close()
		return p.wait()

class DAG(dict):
	def __init__(self,name):
		dict.__init__(self)
		self.update({'dag':{'failFast':False,'tasks':[]}})
		self.name=name
		self.oldmodulename = ''
		self.set_name(name)
	def set_name(self,name):
		self.name=name
		self['name']=name
	def add_dependence(self,module_name,depend,template_name):
		if depend==['']:depend=[]
		if module_name == self.oldmodulename: return
		a_depend={'name':module_name,'dependencies':depend,'template':template_name}
		self['dag']['tasks'].append(a_depend)
		self.oldmodulename = module_name

class Step(dict):
	def __init__(self,name):
		dict.__init__(self)
		self.name=name
		self.set_name(name)
		self.groupnum=-1
		self.update({'name':name,'steps':[]})
	def set_name(self,name):
		self.name=name
		self['name']=name
	def next(self):
		self['steps'].append([])
		self.groupnum+=1
	def add_task(self,name,template,para_dict={}):
		task={'arguments':{'parameters':[]},'name':name,'template':template}
		for i in para_dict:
			task['arguments']['parameters'].append({'name':i,'value':para_dict[i]})
		self['steps'][self.groupnum].append(task)
	def add_loop(self,template,a_para,value_list,name=None):
		if not name:name=self.groupnum
		task={'arguments':{'parameters':[{'name':a_para,'value':'{{item}}'}]},'name':name,'template':template,'withItems':value_list}
		self['steps'][self.groupnum].append(task)
