#!/bin/env python


# *
# DOCUMENT FILE FROM LOG FILES GENERATOR
#
import os, sys, signal
import shutil, glob, re
import json, io 
import zipfile, tarfile
import argparse
import rekdoc, tools
from rekvar import *


##### IMPLEMETATION #####
def clean_files(folder='./temp/'):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        print(file_path)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            return -1

def clean_up(path='./temp/'):
    print('Remove unzip files? (y/n) ', end='')
    choice = input()
    if choice in ['', 'yes', 'y', 'Y', 'yeah', 'YES']:
        clean_files(path)
        return
    return -1 

def clean_up_force(path='./temp/'):
    print('FORCE CLEAN UP DUE TO ERROR!')
    clean_files(path)
    return -1

def check_valid(path):
    return os.path.isdir(path)

def extract_file(serial, compress):
    compress = compress.lower()
    # regex = '*[_.]' + serial + '[_.]*.' + compress
    regex = '*' + serial + '*.' + compress
    file = get_file(regex, root='./sample/') 
    if file == -1: return -1

    print('Extracting: ', file)
    if compress == 'zip':
        unzip(file)
        return tools.rm_ext(file, compress)
    elif compress == 'tar.gz':
        untar(file)
        return tools.rm_ext(file, compress)
    else: return -1

# Find return the file with serial number 
def get_file(regex, root=''):
    path = root + regex
    files = glob.glob(path, recursive=True)
    if len(files) == 0:
        print('No file found matched!')
        return -1
    elif len(files) == 1:
        return files[0]
    else:
        for i in range(len(files)):
            print('[', i, '] ', files[i], sep='')
        c = ''
        while True:
            try:
                c = int(input('Which file?\n [0] ') or '0')
                if c < 0 and c > len(files):
                    continue
            except KeyboardInterrupt:
                print()
                sys.exit()
            except ValueError:
                continue
            break
        return files[c]

def grep(path, regex, single_line=True):
    result = ''
    flag = re.MULTILINE
    pattern = re.compile(regex, flag)
    file = cat(path, False)
    content = file.readlines()

    if single_line:
        for line in range(len(content)):
            if re.search(pattern, content[line]):
                result += content[line].lstrip()
                print(line + 1, ': ', content[line], sep='', end='')
                break 
    else:
        for line in range(len(content)):
            if re.search(pattern, content[line]):
                result += content[line].lstrip()
                print(line + 1, ': ', content[line], sep='', end='')
    print()
    return result

def get_ilom(path):
    print('##### ILOM #####')
    fault = cat(path + FAULT).strip()

    inlet_temp = grep(path + TEMP, 'inlet_temp').strip().split()
    inlet_temp = ' '.join(inlet_temp[2:5])

    exhaust_temp = grep(path + TEMP, 'exhaust_temp').strip().split()
    exhaust_temp = ' '.join(exhaust_temp[2:5])

    firmware = grep(path + FIRMWARE, 'Version').strip().split()
    firmware = ' '.join(firmware[1:])

    print('##### END OF ILOM #####')
    return {'fault': fault, 'inlet': inlet_temp, 'exhaust': exhaust_temp, 'firmware': firmware} 

def get_os(path, os='SOL'):
    x = {}
    if os == 'SOL':
        image = grep(path + IMAGE_SOL, 'Solaris').strip().split()
        image = image[2]
        x['image'] = image

        vol = grep(path + PARTITION_SOL, "\\B\/\\B").strip().split()
        vol = vol[-2]
        vol_avail = 100 - int(vol[:-1])
        x['vol_avail'] = vol_avail

        raid = grep(path + RAID_SOL, "mirror").strip().split()
        if 'ONLINE' in raid:
            raid_stat = True 
        else:
            raid_stat = False
        x['raid_stat'] = raid_stat

        net_ipmp = grep(path + NETWORK_SOL, 'ipmp')
        net_aggr = grep(path + NETWORK_SOL, 'aggr')
        if not net_ipmp and not net_aggr:
            bonding = 'none'
        elif net_ipmp and not net_aggr:
            bonding = 'ipmp'
        elif net_aggr and not net_ipmp:
            bonding = 'aggr'
        else:
            bonding = 'both'
        x['bonding'] = bonding

        cpu_idle = cat(path + CPU_ULTILIZATION_SOL).strip().split('\n')
        cpu_idle = cpu_idle[2]
        cpu_idle = cpu_idle.split()[21]
        cpu_util = 100 - int(cpu_idle)
        x['cpu_util'] = cpu_util

        x['load'] = {}
        load = grep(path + CPU_LOAD_SOL, 'load average').strip().split(', ')
        load_avg = ' '.join(load).split()[-3:]
        load_avg = float((max(load_avg)))
        vcpu = grep(path + VCPU_SOL, 'primary').strip().split()[4]
        vcpu = int(vcpu)
        load_avg_per = load_avg / vcpu
        load_avg_per = float(f'{load_avg_per:.3f}')
        x['load']['load_avg'] = load_avg
        x['load']['vcpu'] = vcpu
        x['load']['load_avg_per'] = load_avg_per

        mem = grep(path + MEM_SOL, 'freelist', False).strip().split()
        mem_free = mem[-1]
        mem_util = 100 - int(mem_free[:-1])
        x['mem_util'] = mem_util

        swap = cat(path + SWAP_SOL).strip().split()
        swap = [swap[8], swap[10]]
        swap[0] = int(swap[0][:-2])
        swap[1] = int(swap[1][:-2])
        swap_util = swap[0] / (swap[0] + swap[1])
        swap_util = int(swap_util * 100)
        x['swap_util'] = swap_util

        print(x)
        print()
    return x

def get_content(node, path):
    root = './temp/'
    orj_path = path[0]
    for i in range(0, len(path)):
        path[i] = root + str(path[i])

    # @@
    ilom = get_ilom(path[0])
    os_info = get_os(path[1], 'SOL')
    name = node

    content = {}
    content[name] = {
            'fault': ilom['fault'],
            'inlet': ilom['inlet'],
            'exhaust': ilom['exhaust'],
            'firmware': ilom['firmware'],
            'image': os_info['image'],
            'vol_avail': os_info['vol_avail'],
            'raid_stat': os_info['raid_stat'],
            'bonding': os_info['bonding'],
            'cpu_util': os_info['cpu_util'],
            'load': os_info['load'],
            'mem_util': os_info['mem_util'],
            'swap_util': os_info['swap_util'],
    }
    print('##### NODE INFORMATION #####')
    print(json.dumps(content, indent = 2))
    print('##### END OF NODE INFORMATION #####\n')
    return content

def cat(path, stdout=True):
    result = ''
    try:
        with open(path, 'r') as file:
            content = file.readlines()
            if stdout:
                count = 0
                for l in content:
                    result += l.lstrip()
                    print(++count + 1, ': ', l, sep='', end='')
                return result
            else: 
                for l in content:
                    result += l.lstrip()
                return io.StringIO(result)
    except Exception as err:
        raise RuntimeError('Cannot open file to read') from err
        return -1

def unzip(file):
    if not zipfile.is_zipfile(file):
        print('Error: Not a zip file')
        return -1
    try:
        with zipfile.ZipFile(file, 'r') as z_object:
            z_object.extractall(path='./temp/')
            print('> UNZIP:', file)
    except Exception as err:
        print('Error:' , err)
        return -1

def untar(file):
    # sucks
    if not tarfile.is_tarfile(file):
        print('Error: Not a tar file')
        return -1
    print(file)
    try:
        with tarfile.open(file, 'r') as t_object:
            try: 
                t_object.extractall(path='./temp/')
                print('> UNTAR:', file)
            except:
                buffer = tools.rm_ext(file, 'tar.gz')
                if clean_up('./temp/' + buffer) == -1:
                    return -1
                t_object.extractall(path='./temp/')
    except Exception as err:
        print(err)
        return -1

def compile(nodes):
    n = len(nodes)
    content_files = []
    for i in range(n):
        path = ['','']
        print('##### EXTRACT FILES #####')
        path[0] = extract_file(nodes[i], 'zip')
        path[1] = extract_file(nodes[i], 'tar.gz')
        print('##### END EXTRACTION #####\n')

        if path == [-1, -1]: 
            print('Error: file not exist!')
            return -1
        print('PATH: ', path)

        
        node = path[1].split('.')[2] # get machine name
        content_files += [node]

        file_name = node
        content = get_content(node, path)
        print(file_name)
        if tools.save_json('./output/' + file_name, content) == -1:
            return -1 
    return content_files 

# FLOW OF PROGRAM
def run(nodes, output):
    content_files = compile(nodes)
    if content_files == -1:
        print('Error: No files to join!')
        return -1

    choice = input('Join all input?[y/n] ')
    if choice in ['', 'yes', 'y', 'Y', 'yeah', 'YES']:
        tools.join_json(content_files, output)

    choice = input('GENERATE DOCUMENT?[y/n] ')
    if choice in ['', 'yes', 'y', 'Y', 'yeah', 'YES']:
        rekdoc.run(output)
##### END_IMPLEMENTATION #####

##### MAIN #####
def main():
    parser = argparse.ArgumentParser(prog='rek', description='Fetch, process data from ILOM and Explorer log files then write them to a report file.',
                                     usage='%(prog)s [options] node [node...]',
                                     epilog='Created by Rek',
                                     exit_on_error=False)
    # group_input = parser.add_mutually_exclusive_group()
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-i', help='file with node names',
                        # nargs='',
                        metavar='file'
                        )
    parser.add_argument('node', help='machine names',
                        nargs='*', 
                        default=None,
                        )
    parser.add_argument('-o', help='output file name',
                        metavar='doc',
                        default='./output/output',
                        )
                       
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", required=False, action="store_true")
    group.add_argument("-q", "--quiet", required=False, action="store_true")
    args = parser.parse_args()

    if (not args.node) and (not args.i):
        parser.parse_args(['-h'])
        return 
    nodes_input = []
    try:
        with open(args.i, 'r') as f:
            line = f.readlines()
            for i in range(len(line)):
                nodes_input.append(line[i].strip())
    except Exception as err:
        print('Invalid or missing input file')

    nodes = nodes_input + args.node
    print(nodes)

    # context = 'Em dado nay co con xem phim not minh\n em daon ay co do an va shopping\n'
    # file = 'ngot.png'
    # tools.drw_text_image(context, file)
    if run(nodes, args.o) == -1: 
        clean_up_force()
        return -1
    clean_up()
    sys.exit()

if __name__ == "__main__":
    main()
##### END_MAIN #####
