from pathlib import Path
# from deepmerge import always_merger
from pathlib import Path
# from deepmerge import always_merger
from typing import List

import deepmerge
import ruamel.yaml

RYCM = ruamel.yaml.comments.CommentedMap

class CommentedMapStrategies(deepmerge.strategy.core.StrategyList):
    NAME = 'CommentedMap'

    @staticmethod
    def strategy_merge(config, path, base, nxt):
        for k, v in nxt.items():
            if k not in base:
                base[k] = v
            else:
                base[k] = config.value_strategy(path + [k], base[k], v)
        try:
            for k, v in nxt.ca.items.items():
                base.ca.items[k] = v
        except AttributeError:
            pass
    
        return base

    @staticmethod
    def strategy_override(config, path, base, nxt):
        """
        move all keys in nxt into base, overriding
        conflicts.
        """
        return nxt

def merge_multi_yaml(yamllist: List[str], out_write_file: str = None ) -> dict:
    # insert as it needs to be before 'dict'
    deepmerge.DEFAULT_TYPE_SPECIFIC_MERGE_STRATEGIES.insert(0, (RYCM, 'merge'))
    Merger = deepmerge.merger.Merger
    Merger.PROVIDED_TYPE_STRATEGIES[RYCM] = CommentedMapStrategies

    always_merger = Merger(deepmerge.DEFAULT_TYPE_SPECIFIC_MERGE_STRATEGIES, ['override'], ['override'])
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    # yaml_object_list = []
    result = {}
    baseinfo = yaml.load(Path(yamllist[0]))
    for one_yaml in yamllist[1:]:
        file_one = Path(one_yaml)
        # yaml_object_list.append(yaml.load(file_one))
        result = always_merger.merge(baseinfo, yaml.load(file_one))

    # result = always_merger.merge(yaml_object_list)
    if out_write_file:
        with open(out_write_file, 'w') as f_out:
            yaml.indent(mapping=4)
            yaml.dump(result, f_out)
    return result