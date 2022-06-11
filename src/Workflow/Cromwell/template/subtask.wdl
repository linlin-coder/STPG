version 1.0
{% for job in children_jobs %}
task {{ job.Name }} {
    input {
        String? docker
        {% for depend in job.Depend %}
        String {{ depend }}_mark
        {% endfor %}
        Int? cpu = {{ job.CPU }}
        String? sge_queue="{{ job.Queue }}"
        String? memory = "{{ job.Memory }}"
        String? sge_mount
    }

    command<<<
        set -e
        set -o
        {% for depend in job.Depend %}
        echo ~{|{{ depend }}_mark}
        echo {{ job.Name }} depend {{ depend }}
        {% endfor %}
        if [[ "{{ job.Status }}" == "done" ]];then
            echo "don't run again";
        else
            singularity run --cleanenv ~{sge_mount} ~{docker} /bin/bash {{ job.Shell_dir }}/{{ job.Module }}_{{ job.Name }}.sh;
        fi
    >>>

    runtime {
        cpu: cpu
        memory: memory
        sge_mount: sge_mount
        sge_queue: sge_queue
    }

    output {
        String {{ job.Name }}_mark = "{{ job.Name }}_mark"
    }
}
{% endfor %}