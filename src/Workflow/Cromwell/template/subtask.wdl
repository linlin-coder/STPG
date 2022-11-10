version 1.0
{% for job in children_jobs %}
task {{ job.Name }} {
    input {
        String docker
    {% for depend in pipelineGraph.getVertex(job).prefix %}
        String {{ depend.id.Name }}_mark
    {% endfor %}
        Int? cpu = {{ job.CPU }}
        String? sge_queue="{{ job.Queue }}"
        String? memory = "{{ job.Memory }}"
        String? sge_mount
    }

    command<<<
        set -e
        set -o
    {% for depend in pipelineGraph.getVertex(job).prefix %}
        echo ~{|{{ depend.id.Name }}_mark}
        echo {{ job.Name }} depend {{ depend.id.Name }}
    {% endfor %}
        if [[ "{{ job.Status }}" == "done" ]];then
            echo "don't run again";
        else
            # docker run --rm --user $(id -u ${USER}):$(id -g ${USER}) -v ~{sge_mount} ~{docker} 
            /bin/sh {{ job.Shell_dir }}/{{ job.Module }}-{{ job.Name }}.sh;
        fi
    >>>

    runtime {
        cpu: cpu
        docker: docker
        memory: memory
        sge_mount: sge_mount
        sge_queue: sge_queue
    }

    output {
        String {{ job.Name }}_mark = "{{ job.Name }}_mark"
    }
}
{% endfor %}