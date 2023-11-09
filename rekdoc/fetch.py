##!/bin/env python
#
# DOCUMENT FILE FROM LOG FILES GENERATOR
#

__version__ = "1.0"
__author__ = "Rek"

# Standard Library
import os
import io
import sys
import shutil
import glob
import json
import zipfile
import tarfile

# Third party library
import click

# Local library
from rekdoc import doc
from rekdoc import tools
from rekdoc.const import *


##### DECORATORS #####
def debug(func):
    def _debug(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"{func.__name__}(args: {args}, kwargs: {kwargs}) -> {result}")
        return result

    return _debug


##### END OF DECORATORS #####


##### IMPLEMETATION #####
# TODO: REWRITE for Windows compatibility
def clean_files(dir, verbose):
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)
        if verbose:
            click.secho("Deleted: " + file_path)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            click.secho("Failed to delete %s. Reason: %s" % (file_path, e), fg=ERROR)
            return -1


def clean_up(path, prompt="Remove files?", verbose=False, force=False):
    if force:
        clean_files(path, verbose)
    else:
        choice = click.confirm(click.style(prompt, fg=ERROR), default="y")
        if choice:
            clean_files(path, verbose)
        return


def clean_up_force(path):
    click.secho("FORCE CLEAN UP DUE TO ERROR!", fg=ERROR)
    clean_files(path)
    return -1


def check_valid(path):
    return os.path.isdir(path)


##### IMAGE PROCESSING #####
## DRAW ILOM ##
def drw_fault(path, out_dir, debug):
    fault = io.StringIO()
    fault.write(path + FAULT + "\n")
    fault.write(tools.cat(os.path.normpath(path + FAULT), debug=debug))
    tools.drw_text_image(fault, os.path.normpath(out_dir + "/fault.png"))


def drw_temp(path, out_dir, debug):
    temp = io.StringIO()
    temp.write(path + TEMP + "\n")
    reg = "^ /System/Cooling$"
    temp.write(tools.grep(os.path.normpath(path + TEMP), reg, False, 8, debug))
    tools.drw_text_image(temp, os.path.normpath(out_dir + "/temp.png"))


def drw_firmware(path, out_dir, debug):
    firmware = io.StringIO()
    firmware.write(path + FIRMWARE + "\n")
    reg = "^Oracle"
    firmware.write(tools.grep(os.path.normpath(path + FIRMWARE), reg, True, 5, debug))
    tools.drw_text_image(firmware, os.path.normpath(out_dir + "/firmware.png"))


def drw_ilom(path, out_dir, verbose=False, debug=False):
    drw_fault(path, out_dir, debug)
    drw_temp(path, out_dir, debug)
    drw_firmware(path, out_dir, debug)

    return ["fault.png", "temp.png", "firmware.png"]


## END DRAW ILOM ##


## DRAW OF ##
def drw_image(path, out_dir, debug):
    image = io.StringIO()
    image.write(path + IMAGE_SOL + "\n")
    image.write(tools.cat(os.path.normpath(path + IMAGE_SOL), debug=debug))
    tools.drw_text_image(image, os.path.normpath(out_dir + "/image.png"))
    return image


def drw_vol(path, out_dir, debug):
    vol = io.StringIO()
    vol.write(path + PARTITION_SOL + "\n")
    vol.write(tools.cat(os.path.normpath(path + PARTITION_SOL), debug=debug))
    tools.drw_text_image(vol, os.path.normpath(out_dir + "/vol.png"))
    return vol


def drw_raid(path, out_dir, debug):
    raid = io.StringIO()
    raid.write(path + RAID_SOL + "\n")
    raid.write(tools.cat(os.path.normpath(path + RAID_SOL), debug=debug))
    tools.drw_text_image(raid, os.path.normpath(out_dir + "/raid.png"))
    return raid


def drw_net(path, out_dir, debug):
    net = io.StringIO()
    net.write(path + NETWORK_SOL + "\n")
    net.write(tools.cat(os.path.normpath(path + NETWORK_SOL), debug=debug))
    tools.drw_text_image(net, os.path.normpath(out_dir + "/net.png"))
    return net


def drw_cpu(path, out_dir, debug):
    cpu_idle = io.StringIO()
    cpu_idle.write(path + CPU_ULTILIZATION_SOL + "\n")
    cpu_idle.write(
        tools.cat(os.path.normpath(path + CPU_ULTILIZATION_SOL), debug=debug)
    )
    tools.drw_text_image(cpu_idle, os.path.normpath(out_dir + "/cpu_idle.png"))
    return cpu_idle


def drw_load(path, out_dir, debug):
    load = io.StringIO()
    load.write(path + CPU_LOAD_SOL + "\n")
    load.write(tools.cat(os.path.normpath(path + CPU_LOAD_SOL), debug=debug))
    tools.drw_text_image(load, os.path.normpath(out_dir + "/load.png"))
    return load


def drw_mem(path, out_dir, debug):
    mem = io.StringIO()
    mem.write(path + MEM_SOL + "\n")
    mem.write(tools.cat(os.path.normpath(path + MEM_SOL), debug=debug))
    tools.drw_text_image(mem, os.path.normpath(out_dir + "/mem.png"))
    return mem


def drw_swap(path, out_dir, debug):
    swap = io.StringIO()
    swap.write(path + SWAP_SOL + "\n")
    swap.write(tools.cat(os.path.normpath(path + SWAP_SOL), debug=debug))
    tools.drw_text_image(swap, os.path.normpath(out_dir + "/swap.png"))
    return swap


# SUCKS, rewrite later
def drw_os(path, out_dir, verbose=False, debug=False):
    drw_image(path, out_dir, debug)
    drw_vol(path, out_dir, debug)
    drw_raid(path, out_dir, debug)
    drw_net(path, out_dir, debug)
    drw_cpu(path, out_dir, debug)
    drw_load(path, out_dir, debug)
    drw_mem(path, out_dir, debug)
    drw_swap(path, out_dir, debug)
    return [
        "image.png",
        ["vol.png", "raid.png"],
        "net.png",
        "cpu_idle.png",
        "load.png",
        "mem.png",
        "swap.png",
    ]


def drw_content(path, output, verbose=False, debug=False):
    ilom = drw_ilom(path[0], output, verbose=False, debug=debug)
    os_info = drw_os(path[1], output, verbose=False, debug=debug)
    images = ilom + os_info
    if debug:
        print(images)
    return images


def extract_file(serial, compress, verbose, force):
    compress = compress.lower()
    regex = "*" + serial + "*." + compress
    file = get_file(regex, root="./sample/")
    if file == -1:
        return -1

    if compress == "zip":
        unzip(file, verbose, force)
        dir = tools.rm_ext(file, compress)
        path = os.path.split(dir)[1]
        return path
    elif compress == "tar.gz":
        untar(file, verbose, force)
        dir = tools.rm_ext(file, compress)
        path = os.path.split(dir)[1]
        return path
    else:
        return -1


# Find return the file with serial number
def get_file(regex, root=""):
    path = root + regex
    files = glob.glob(path, recursive=True)
    if len(files) == 0:
        print("No file found matched!")
        return -1
    elif len(files) == 1:
        return files[0]
    else:
        for i in range(len(files)):
            print("[", i, "] ", files[i], sep="")
        c = ""
        while True:
            try:
                c = int(input("Which file?\n [0] ") or "0")
                if c < 0 and c > len(files):
                    continue
            except KeyboardInterrupt:
                print()
                sys.exit()
            except ValueError:
                continue
            break
        return files[c]


##### FETCH ILOM ######
def get_fault(path, debug):
    fault = tools.cat(os.path.normpath(path + FAULT), debug=debug).strip()
    return fault


def get_temp(path, debug):
    inlet_temp = (
        tools.grep(os.path.normpath(path + TEMP), "inlet_temp", True, debug=debug)
        .strip()
        .split()
    )
    inlet_temp = " ".join(inlet_temp[2:5])

    exhaust_temp = (
        tools.grep(os.path.normpath(path + TEMP), "exhaust_temp", True, debug=debug)
        .strip()
        .split()
    )
    exhaust_temp = " ".join(exhaust_temp[2:5])
    return inlet_temp, exhaust_temp


def get_firmware(path, debug):
    firmware = (
        tools.grep(os.path.normpath(path + FIRMWARE), "Version", True, debug=debug)
        .strip()
        .split()
    )
    firmware = " ".join(firmware[1:])
    return firmware


def get_ilom(path, verbose, debug=False):
    fault = get_fault(path, debug)
    inlet_temp, exhaust_temp = get_temp(path, debug)
    firmware = get_firmware(path, debug)

    return {
        "fault": fault,
        "inlet": inlet_temp,
        "exhaust": exhaust_temp,
        "firmware": firmware,
    }


#####


##### FETCH OS ######
def get_image(path, debug):
    image = (
        tools.grep(os.path.normpath(path + IMAGE_SOL), "Solaris", True, debug=debug)
        .strip()
        .split()
    )
    image = image[2]
    return image


def get_vol(path, debug):
    vol = (
        tools.grep(os.path.normpath(path + PARTITION_SOL), "\\B\/$", True, debug=debug)
        .strip()
        .split()
    )
    vol = vol[-2]
    return vol


def get_raid(path, debug):
    raid = (
        tools.grep(os.path.normpath(path + RAID_SOL), "mirror", True, debug=debug)
        .strip()
        .split()
    )
    if "ONLINE" in raid:
        raid_stat = True
    else:
        raid_stat = False
    return raid_stat


def get_bonding(path, debug):
    net_ipmp = tools.grep(os.path.normpath(path + NETWORK_SOL), "ipmp", True, debug)
    net_aggr = tools.grep(
        os.path.normpath(path + NETWORK_SOL), "aggr", True, debug=debug
    )

    if not net_ipmp and not net_aggr:
        bonding = "none"
    elif net_ipmp and not net_aggr:
        bonding = "ipmp"
    elif net_aggr and not net_ipmp:
        bonding = "aggr"
    else:
        bonding = "both"
    return bonding


def get_cpu_util(path, debug):
    cpu_idle = (
        tools.cat(os.path.normpath(path + CPU_ULTILIZATION_SOL), debug=debug)
        .strip()
        .split("\n")
    )
    cpu_idle = cpu_idle[2]
    cpu_idle = cpu_idle.split()[21]
    cpu_util = 100 - int(cpu_idle)
    return cpu_idle, cpu_util


def get_load_avg(path, debug):
    load = (
        tools.grep(
            os.path.normpath(path + CPU_LOAD_SOL), "load average", True, debug=debug
        )
        .strip()
        .split(", ")
    )
    load_avg = " ".join(load).split()[-3:]
    load_avg = float((max(load_avg)))
    return load_avg


def get_vcpu(path, debug):
    vcpu = (
        tools.grep(os.path.normpath(path + VCPU_SOL), "primary", True, debug=debug)
        .strip()
        .split()[4]
    )
    vcpu = int(vcpu)
    return vcpu


def get_load(path, debug):
    load_avg = get_load_avg(path, debug)
    vcpu = get_vcpu(path, debug)
    load_avg_per = load_avg / vcpu
    load_avg_per = float(f"{load_avg_per:.3f}")
    return load_avg, vcpu, load_avg_per


def get_mem_util(path, debug):
    mem = (
        tools.grep(os.path.normpath(path + MEM_SOL), "freelist", True, debug=debug)
        .strip()
        .split()
    )
    mem_free = mem[-1]
    mem_util = 100 - int(mem_free[:-1])
    return mem_free, mem_util


def get_swap_util(path, debug):
    swap_free = (
        tools.cat(os.path.normpath(path + SWAP_SOL), debug=debug).strip().split()
    )
    swap_free = [swap_free[8], swap_free[10]]
    swap_free[0] = int(swap_free[0][:-2])
    swap_free[1] = int(swap_free[1][:-2])
    swap_util = swap_free[0] / (swap_free[0] + swap_free[1])
    swap_util = int(swap_util * 100)

    return swap_free, swap_util


def get_os(path, os_name="SOL", verbose=False, debug=False):
    x = {}
    if os_name == "SOL":
        image = get_image(path, debug)

        vol = get_vol(path, debug)
        vol_avail = 100 - int(vol[:-1])
        x["image"] = image
        x["vol_avail"] = vol_avail

        raid_stat = get_raid(path, debug)
        x["raid_stat"] = raid_stat

        bonding = get_bonding(path, debug)
        x["bonding"] = bonding

        cpu_util = get_cpu_util(path, debug)[1]
        x["cpu_util"] = cpu_util

        load = get_load(path, debug)
        x["load"] = {}
        x["load"]["load_avg"] = load[0]
        x["load"]["vcpu"] = load[1]
        x["load"]["load_avg_per"] = load[2]

        mem_util = get_mem_util(path, debug)[1]
        x["mem_util"] = mem_util

        swap_util = get_swap_util(path, debug)[1]
        x["swap_util"] = swap_util

    return x


##### FETCH OS ######


def get_content(node, path, verbose):
    # @@
    ilom = get_ilom(path[0], verbose)
    os_info = get_os(path[1], "SOL", verbose)
    # print(json.dumps(ilom, indent=2))
    # print(json.dumps(os_info, indent=2))
    name = node

    content = {}
    content[name] = {
        "fault": ilom["fault"],
        "inlet": ilom["inlet"],
        "exhaust": ilom["exhaust"],
        "firmware": ilom["firmware"],
        "image": os_info["image"],
        "vol_avail": os_info["vol_avail"],
        "raid_stat": os_info["raid_stat"],
        "bonding": os_info["bonding"],
        "cpu_util": os_info["cpu_util"],
        "load": os_info["load"],
        "mem_util": os_info["mem_util"],
        "swap_util": os_info["swap_util"],
    }
    if verbose:
        print(json.dumps(content, indent=2))
    return content


def unzip(file, verbose, force):
    if not zipfile.is_zipfile(file):
        print("Error: Not a zip file")
        return -1
    if verbose:
        print("Extracting: " + file)
    try:
        with zipfile.ZipFile(file, "r") as zip:
            try:
                zip.extractall(path="temp/")
            except IOError as err:
                clean_up(
                    os.path.normpath(
                        "temp/" + os.path.split(tools.rm_ext(file, "zip"))[1]
                    ),
                    force=force,
                )
                zip.extractall(path="temp/")
    except IOError as err:
        print(err)
        return -1


def untar(file, verbose, force):
    if not tarfile.is_tarfile(file):
        print("Error: Not a tar file")
        return -1
    if verbose:
        print("Extracting: " + file)
    try:
        with tarfile.open(file, "r") as tar:
            for f in tar.getmembers():
                try:
                    tar.extract(f, set_attrs=False, path="temp/")
                except IOError:
                    continue
                except Exception as err:
                    click.echo(err)
                    return -1
    except IOError as err:
        print(err)
        return -1


def compile(nodes, root, verbose, force):
    n = len(nodes)
    content_files = []
    for node in nodes:
        create_dir(root + "/" + node, verbose=verbose, force=force)

    for node in nodes:
        progress_bar = click.progressbar(
            range(100),
            label=click.style(node, fg=SECTION),
            fill_char="*",
            empty_char=" ",
            show_eta=False,
        )
        path = ["", ""]
        path[0] = extract_file(node, "zip", verbose, force)
        path[1] = extract_file(node, "tar.gz", verbose, force)
        progress_bar.update(20)

        if path == [-1, -1]:
            print("Error: file not exist!")
            return -1
        if verbose:
            print("EXTRACTED FILES: ", path)

        content_files += [node]
        progress_bar.update(20)

        file_name = node
        for i in range(0, len(path)):
            path[i] = os.path.normpath("temp/" + str(path[i]))
        content = get_content(node, path, verbose=verbose)
        progress_bar.update(20)

        # DRAW IMAGES FOR CONTENT
        images = drw_content(
            path, os.path.normpath(root + "/" + node + "/"), verbose=verbose
        )
        progress_bar.update(20)
        # END DRAWING
        if (
            tools.save_json(
                os.path.normpath(root + "/" + node + "/" + node + ".json"), content
            )
            == -1
        ):
            return -1
        if (
            tools.save_json(
                os.path.normpath(root + "/" + node + "/images.json"), images
            )
            == -1
        ):
            return -1

        progress_bar.update(20)
        click.secho(" ", nl=False)
        click.secho("DONE", bg=SUCCESS, fg="black")
        progress_bar.finish()
        if verbose:
            click.echo()
    return content_files


def create_dir(path, verbose=False, force=False):
    try:
        os.mkdir(os.path.normpath(path))
        if verbose:
            click.secho("\nFolder created: " + path)
    except FileExistsError as err:
        if not os.listdir(path):
            return
        if force:
            clean_up(
                path=os.path.normpath(path),
                prompt="Do you want to replace it?",
                force=force,
            )
        else:
            click.secho(click.style(path, fg=SECTION) + " folder exist!")
            clean_up(
                path=os.path.normpath(path),
                prompt="Do you want to replace it?",
                force=force,
            )


# FLOW OF PROGRAM
def run(nodes, output, verbose, force):
    out_dir = os.path.split(output)[0]

    # create output and temp directory
    create_dir(os.path.normpath(out_dir), verbose, force)
    create_dir(os.path.normpath("temp"), verbose, force=True)

    # fetch and cook to images from logs
    content_files = compile(nodes, out_dir, verbose, force)
    if content_files == -1:
        click.secho("Error: ", fg=ERROR, nl=False)
        click.echo("No files to join!")
        return -1

    # union all jsons to one file
    tools.join_json(content_files, output)


##### END_IMPLEMENTATION #####


##### MAIN #####
@click.group()
def main():
    click.echo("duh")
    pass


if __name__ == "__main__":
    main()
##### END_MAIN #####
