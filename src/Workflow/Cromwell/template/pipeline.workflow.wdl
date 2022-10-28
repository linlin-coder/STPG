version 1.0

# import "./Fastqc/fqtools.task.wdl" as fqtools
{% for modules in pipeline_jobs %}
{% for jobs in pipeline_jobs[modules] %}
import "./{{ modules }}/{{ jobs }}.task.wdl" as {{ jobs }}
{% endfor %}
{% endfor %}
import "./common/struct.wdl" as structs
workflow pipeline{
	input{
		File config_json
		String? sge_mount
		String? workid
		String? ossdir
	}
	ModuleConfig m_config= read_json(config_json)
    Parameter config_common = m_config.module["common"]
	###########  {{ jobs }} start ##############
{% for modules in pipeline_jobs %}
{% for jobs in pipeline_jobs[modules] %}
	{% for job in pipeline_jobs[modules][jobs] %}
	call {{ jobs }}.{{ job.Name }}  as  {{ job.Name }} {
		input:
			sge_mount = sge_mount,
			docker = "{{ job.Image }}",
			{% for depend in job.Depend %}
			{{ depend }}_mark =  {{ depend }}.{{ depend }}_mark,
			{% endfor %}
	}
	{% endfor %}

	###########  {{ jobs }} end ##############
{% endfor %}
{% endfor %}
	parameter_meta{
		FQ1: {description: "",
			required: "True",
			category:"input"}
	}
	meta{
		author:"linlin-coder"
		name: "xxx"
		version: "V1.0"
		mail : "xxx"
	}

}
