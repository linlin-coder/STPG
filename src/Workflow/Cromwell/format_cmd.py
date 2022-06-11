import re

pat2=re.compile('{(\\S+?)(\\[\\d+\\])}')

def parser_command(one_command):
    #'{a} ~{{b}}'.format(a=1)
    # cmd = '{make} -f sample_id={Part[0]} sample_id2={Part[1]} merge_data'
    num_list = iter(list(range(100)))
    iter_variation = pat2.finditer(one_command)
    for variation in iter_variation:
        one_command = one_command.replace(variation.group(),'variation'+str(next(num_list)))

    return one_command