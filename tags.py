import sys
import os
import glob
from pathlib import Path
import ruamel.yaml

post_dir = '_posts/'
tag_dir = 'tags/'

filenames = glob.glob(post_dir + '*md')
total_tags = []
for filename in filenames:
    path = Path(filename)
    yaml_str, markdown = path.read_text().lstrip().split('\n---', 1)
    yaml_str += '\n' # re-add the trailing newline that was split off

    yaml = ruamel.yaml.YAML()
    yaml.explicit_start = True
    data = yaml.load(yaml_str)

    total_tags = total_tags + data['tags']

total_tags = set(total_tags)

old_tags = glob.glob(tag_dir + '*.md')
for tag in old_tags:
    os.remove(tag)
    
if not os.path.exists(tag_dir):
    os.makedirs(tag_dir)

for tag in total_tags:
    tag_filename = tag_dir + tag + '.md'
    f = open(tag_filename, 'a')
    write_str = '---\nlayout: tag\ntitle: \"Tag: ' + tag + '\"\ntag: ' + tag + '\nrobots: noindex\n---\n'
    f.write(write_str)
    f.close()
print("Tags generated, count", total_tags.__len__())
