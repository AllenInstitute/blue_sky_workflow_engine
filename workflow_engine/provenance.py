class Provenance(object):
    @classmethod
    def pip_freeze_dependencies(cls, file_path):
        with open(file_path,'r') as f:
            deps = []
            for l in f.readlines():
                try:
                    package,version = l.strip().split('==')
                    entry = { 'name': package }
                    version_numbers = version.split('.')
                    if len(version_numbers) == 3:
                        entry['version'] = {
                            'major': version_numbers[0],
                            'minor': version_numbers[1],
                            'patch': version_numbers[2]
                        }
                    elif len(version_numbers) == 2:
                        entry['version'] = {
                            'major': version_numbers[0],
                            'minor': version_numbers[1],
                        }
                    deps.append(entry)
                except:
                    pass
        return deps