
"""
0xA2_chess-engine
Copyright (C) 2020-2021  Ofek Shochat

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from time import time
st = time()
from os.path import relpath
from glob import glob
import os
import xxhash
import subprocess
from threading import Thread
from sys import argv

# defaults
directory = "src"
name = "main.exe"
warn_level = 2
significants = {"C4244":2, "C4530:":0}

FNULL = open(os.devnull, 'w')

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RESET = "\033[39m"

def get_children(path):
    ds = []
    for i in glob(path + "\\*"):
        if i.count(".") < 2:
            dd = get_children(i)
            for d in dd:
                ds.append(d)
        else:
            ds.append(i)
        
    return ds
# get all file dirs (all tree)

class f:
    def __init__(self, text, name):
        self.text = text
        self.once = False
        self.name = name
        self.deps = 0
        self.dds = []

# new plan: iterating over the includes. searching for the include in g_dirs (local include) and then doing `deps += 1` 
# and doing that for every thing in that file for every file. not efficiant but works
 
def get_includes(path, curr, g_dirs):
    try:
        for i in open(path, encoding="utf-8").readlines():
            if i[0:11].__contains__("#include \""):
                curr.deps += 1
                curr.dds.append(i[11:-1])
                for d in g_dirs:
                    if d.split('\\')[-1] == i[11:-1]:
                        get_includes(d, curr, g_dirs)
    except UnicodeDecodeError:
        for i in open(path, encoding="ISO-8859-1").readlines():
            if i[0:11].__contains__("#include \""):
                curr.deps += 1
                curr.dds.append(i[11:-1])
                for d in g_dirs:
                    if d.split('\\')[-1] == i[11:-1]:
                        get_includes(d, curr, g_dirs)

def get_files(name):
    dirs = glob(".\\{}\\*".format(directory))
    g_dirs = []
    for i in dirs:
        if i.count(".") < 2:
            dd = get_children(i)
            for i in dd:
                g_dirs.append(i)   
        else:
            g_dirs.append(i)

    fs = []
    for t in g_dirs:
        curr = f(hash(t), t)
        get_includes(t, curr, g_dirs)
        fs.append(curr)
    
    ss = sorted(fs, key=lambda i: i.deps)
    for d in range(len(ss)):
        try:
            if ss[d].deps == ss[d+1].deps:
                filename, file_extension = os.path.splitext(ss[d+1].name)
                if filename + ".h" in ss[d].dds:
                    ss[d+1], ss[d] = ss[d], ss[d+1]
            """if ss[d].name == argv[argv.index("-main")+1]:
                ss.insert(len(ss),ss[d])
                del ss[d]"""

        except IndexError:
            break
    
    files = []
    for i in ss:
        filename, file_extension = os.path.splitext(i.name)
        if file_extension == ".cc" or file_extension == ".cpp":
            files.append(i.name)
    return files

def asstr(l):
    string = ""
    for i in l:
        string += str(i) + " "
    return string

a = 0

def issignificant(s):
    a = significants
    for i in a:
        if i in s:
            return a[i]
    return -1

def miliseconds():
    return int((time() - st)*1000)

def onecomp(f, files, rules, i, FNULL):
    global a
    filename = os.path.basename(f)[:os.path.basename(f).find(".")]
    ssa = subprocess.check_output("cl /c \"/Fo./build/objs/{}.obj\" /O2 \"{}\" {} /W2".format(filename, f, asstr(rules)), stderr=FNULL).decode("utf-8")
    print("[{}][{}/{}] compiled {}                       ".format(miliseconds(), a, len(files)+1, f), end="\r")
    a += 1
    if "warning C4244" in ssa:
        #d.write(i[i.find("warning"):i.find("\n")] + "\n")
        ssa = ssa.split("\r\n")
        for ss in ssa:
            sig = issignificant(ss)
            if sig >= warn_level:
                print()
                print("with(wl:%s)" % sig, ss[ss.find(": ")+2:])
                
                
def comp(files, out, rules):
    threads = []
    print("[{}][?/{}] started building {}".format(miliseconds(), len(files)+1, out), end="\r")
    for i in range(len(files)):
        t = Thread(target=onecomp, args=[files[i], files, rules, i, FNULL])
        t.deamon = True
        t.start()
        threads.append(t)
    while threads[-1].is_alive():
        pass
    
    linkfiles = glob("./build/objs/*.obj")
    link = ""
    for i in linkfiles:
        link += i + " "
    print("[{}/{}] linking final {}                       ".format(len(files), len(files)+1, out), end="\r")
    subprocess.check_output("link -OUT:{} {} {}".format("./build/" + out, link, asstr(linkrules))).decode("utf-8")
    print("[{}][{}/{}] final build: {}                       ".format(miliseconds(), len(files)+1, len(files)+1, out), end="\r")

def getRules():
    global linkrules
    rules = []
    linkrules = []
    def filedirectory(path):
        global directory
        directory = path
    
    def exename(exename):
        global name
        name = exename

    def additional_include(path, compiler="cl"):
        if compiler == "cl":
            rules.append("/I{}".format(path))
        elif compiler == "gcc":
            rules.append("-I '{}'".format(path))
    
    def libs(*libpaths):
        for i in libpaths:
            linkrules.append("/LIBPATH:\"{}\"".format(i))

    for i in open("poop.builder").readlines():
        exec(i)
    return rules

def wipeobjs():
    files = glob('build/objs/*.obj')
    for f in files:
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))

def wipe():
    open("./build/build.options", "w")

def getHashes(files):
    hashes = {}
    for i in files:
        hashes.update({i:xxhash.xxh32(bytes(open(i).read(), "utf-8")).hexdigest()})
    return hashes

def getChanged(files, previoushashes, hashes):
    changedFiles = []
    for i in previoushashes:
        try:
            if previoushashes[i] != hashes[i]:
                changedFiles.append(i)
        except IndexError:
            changedFiles.append(i)
    return changedFiles

def cc_compiler_test(): # getCompiler()

    """
    try:
        subprocess.check_call(preferedCompiler, stderr=FNULL, stdout=FNULL)
    except:
        info("[info] prefered compiler({}) is not available.".format(preferedCompiler))
        for i in supported_compilers
            try:
                subprocess.check_call(i, stderr=FNULL, stdout=FNULL)
                break
            except FileNotFoundError:
                info("[info] {} is not available.".format(i))
    return i
    """
    try:
        subprocess.check_call("cl", stderr=FNULL, stdout=FNULL)
    except FileNotFoundError:
        print("0x2E7" + FAIL + "[ERROR] " + RESET + "cl was not found.")
        exit(1)

def main():

    cc_compiler_test()

    if "--wipe" in argv:
        wipe()
        wipeobjs()

    rules = getRules()

    if not os.path.isdir("build"): os.mkdir("build")
    if not os.path.isdir("build/objs"): os.mkdir("build/objs")
    if not os.path.exists("./build/build.options"): open("./build/build.options", 'a').close()
    if open("./build/build.options", "r+").read() == "": 
        create = True
        #f = open("./build/build.options", "w+")
    else: 
        create = False
    f = open("./build/build.options", "a")
    write = ""

    r = open("./build/build.options").readlines()
    files = get_files(directory)
    hashes = getHashes(files)
    if create: 
        for i in hashes:
            write += "%s:%s\2" % (i, hashes[i])
        write += "\n"
        comp(files, name, rules)
    else:
        previoushashes = {}
        for i in r[0].split("\2")[:-1]:
            d = i.split(":")
            previoushashes.update({d[0]:d[1]})
        if previoushashes == hashes:
            print("up to date")
            exit(0)
        else:
            print("Detected a change")
            comp(getChanged(files, previoushashes, hashes), name, rules)
            hashes = getHashes(files)
            wipe()
            for i in hashes:
                write += "%s:%s\2" % (i, hashes[i])
            write += "\n"
    print()
    f.write(write)

main()