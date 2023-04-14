#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import json
import sys # sys.argv
import getopt # getopt
import hashlib # md5 sha1
import configparser # ini (python 3.0 use configparser)
import fcntl # file lock
import datetime # format file modify time
gDefaultPath = "../execution/glsl"
gOutputHeadFile = "../shaders/AllShader.h"
gOutputSourceFile = "AllShader.cpp"


def findAllShader(path):
    cmd = "find " + path + " -name \"*.comp\""
    vexs = os.popen(cmd).read().split('\n')
    output = []
    for f in vexs:
        if len(f) > 1:
            output.append(f)
    return output


def getName(fileName):
    s1 = fileName.replace("/", "_")
    s1 = s1.replace(".", "_")
    s1=s1.replace("__","_")
    return s1


def generateFileAsm(headfile, sourcefile, asmdirs):
    cmd = "find " + asmdirs + " -name \"*.spirv\""
    vexs = os.popen(cmd).read().split('\n')
    output = []
    for f in vexs:
        if len(f) > 1:
            output.append(f)
    h = "#ifndef SPRIV_SHADER_AUTO_GENERATE_H\n#define SPRIV_SHADER_AUTO_GENERATE_H\n"

    cpp = "#include \"" + headfile + "\"\n"
    for s in output:
        name = getName(s)
        print(name)
        print(os.popen("spirv-as " + s + " -o tempspv --target-env vulkan1.0").read())
        h += "extern const unsigned char " + name + "[];\n"
        h += 'extern unsigned int ' + name + '_len;\n'
        print(os.popen("xxd -i tempspv > temp.spv.cpp").read())
        with open('temp.spv.cpp') as f:
            allContent = f.read().replace('tempspv', name)
        cpp += 'const ' + allContent + '\n'
    h += "#endif"
    with open(headfile, "w") as f:
        f.write(h)
    with open(sourcefile, "w") as f:
        f.write(cpp)
    os.popen('rm temp.spv.cpp').read()
    os.popen('rm tempspv').read()


class ShaderFile:

    def __init__(self, shader='', ref=False, raw=''):
        self.shaderFile = shader  # string , source .comp file
        self.refFile = ref  # bool , reference file , org file not exists ,auto generated by script
        self.rawRefFile = raw  # string , if isRefFile this value point out raw file name else empty
        self.spirvFile = ''  # string, spir-v file
        self.spirvCacheFile = ''  # string, spir-v cache file
        self.appendMacro = ''  # string, append macro content if isRefFile is true

    def getShaderFile(self):
        return self.shaderFile

    def getRawRefFile(self):
        if (None == self.rawRefFile):
            return ''
        return self.rawRefFile

    def getFileName(self):
        s = self.shaderFile.split('glsl')
        s1 = 'glsl'+s[1]
        s1 = s1.replace("/", "_")
        s1 = s1.replace(".", "_")
        return s1

    def isRefFile(self):
        return self.refFile

    def setMacro(self, macro):
        self.appendMacro = macro

    def getMacro(self):
        return self.appendMacro

    def getSpirvFile(self):
        return self.spirvFile

    def setSpirvFile(self,f):
        self.spirvFile = f

    def getSpirvCacheFile(self):
        return self.spirvCacheFile

    def setSpirvCacheFile(self,f):
        self.spirvCacheFile = f

class ShaderCache:

    # make dirs
    def __checkDir__(self,dir):
        if not os.path.exists(dir) :
            os.makedirs(dir)
        if not os.path.isdir(dir) :
            print('cache dir %s exists but it is a file not a directory, please check! \n' % dir)
            return False
        return True

    def __checkCacheDirs__(self):
        if not self.__checkDir__(self.root_dir):
            return False
        dir = os.path.join(self.root_dir, self.shader_dir)
        if not self.__checkDir__(dir):
            return False
        dir = os.path.join(self.root_dir, self.shader_dir,self.cache_dir)
        if not self.__checkDir__(dir):
            return False
        return True

    def __calcFileCheckInformation__(self,f):
        f = f.encode('utf-8')
        ck_size = os.path.getsize(f)
        ck_size = '%d' %ck_size
        ck_mtime = os.path.getmtime(f)
        ck_lastmodify = datetime.datetime.fromtimestamp(ck_mtime).strftime('%Y-%m-%d %H:%M:%S %f')
        ck_md5 = hashlib.md5(f)
        ck_sha1 = hashlib.sha1(f)
        return ck_size,ck_lastmodify,ck_md5.hexdigest(),ck_sha1.hexdigest()

    def __readShaderFileConfigInformation__(self,shader):
        sha1 = ''
        md5 = ''
        size = 0
        lastmodify = ''
        spirv_file = ''
        spirv_size = 0
        spirv_sha1 = ''
        spirv_md5 = ''
        spirv_lastmodify = ''
        if self.configParser.has_section(shader) :
            sha1 = self.configParser.get(shader,'sha1')
            md5 = self.configParser.get(shader,'md5')
            size = self.configParser.getint(shader, 'size')
            lastmodify = self.configParser.get(shader, 'lastmodify')
            spirv_file =  self.configParser.get(shader, 'spirv_file')
            spirv_size = self.configParser.getint(shader, 'spirv_size')
            spirv_sha1 = self.configParser.get(shader, 'spirv_sha1')
            spirv_md5 = self.configParser.get(shader, 'spirv_md5')
            spirv_lastmodify = self.configParser.get(shader, 'spirv_lastmodify')
        return sha1, md5, size, lastmodify, spirv_file, spirv_size, spirv_sha1, spirv_md5, spirv_lastmodify

    def __readConfigInformation__(self):
        self.cache_valid = False
        sh_section = self.scriptName
        if self.configParser.has_section(sh_section) :
            self.sha1 = self.configParser.get(sh_section,'sha1')
            self.md5 = self.configParser.get(sh_section,'md5')
            self.size = self.configParser.getint(sh_section, 'size')
            self.lastmodify = self.configParser.get(sh_section, 'lastmodify')

            # check information
            sc_size,lastmodify,sc_md5,sc_sha1 = self.__calcFileCheckInformation__(sh_section)
            if (sc_size == self.size) and (lastmodify == self.lastmodify) and (sc_md5 == self.md5) and (sc_sha1 == self.sha1) :
                self.cache_valid = True


    def __loadConfigFile__(self):
        if not self.__checkCacheDirs__() :
            return False

        if os.path.isfile(self.configFile):
            self.__readConfigInformation__()


        return True

    def initlizateShaderCache(self):

        if not self.__loadConfigFile__():
            return False

        return True

    def __setupSpirvCacheFiles__(self,objs):
        for obj in objs:
            if obj.isRefFile():
                shader = obj.getRawRefFile()
                cache_name = obj.getShaderFile()
                name, ext = os.path.splitext(os.path.basename(cache_name))
            else :
                shader = obj.getShaderFile()
                name, ext = os.path.splitext(os.path.basename(shader))
            cache_path = os.path.join(self.root_dir, self.shader_dir, self.cache_dir, name + '.spv')
            obj.setSpirvFile('')
            obj.setSpirvCacheFile(cache_path)

    def setupShaderCache(self,objs):

        if not self.use_cache :
            return
        # cache invalid ,we setup cache file path
        # if not self.cache_valid :
        #     self.__setupSpirvCacheFiles__(objs)
        #     return

        for obj in objs:
            shader = obj.getShaderFile()
            refFile = shader
            if obj.isRefFile():
                cache_name = obj.getShaderFile()
                name, ext = os.path.splitext(os.path.basename(cache_name))
                refFile = obj.getRawRefFile()
            else :
                name, ext = os.path.splitext(os.path.basename(shader))
            cache_path = os.path.join(self.root_dir, self.shader_dir, self.cache_dir, name + '.spv')
            sha1, md5, size, lastmodify, spirv_file, spirv_size, spirv_sha1, spirv_md5, spirv_lastmodify = self.__readShaderFileConfigInformation__(shader)
            if len(sha1)<=0 or len(md5)<=0 or size<=0 or len(spirv_file) <= 0 or spirv_size <=0 or len(spirv_md5) <= 0 \
                    or len(spirv_lastmodify) <= 0 or (not os.path.isfile(refFile)) or (not os.path.isfile(spirv_file)) :
                    obj.setSpirvFile('')
                    obj.setSpirvCacheFile(cache_path)
            else :
                ck_size, ck_lastmodify, ck_md5, ck_sha1 = self.__calcFileCheckInformation__(refFile)
                sp_ck_size, sp_ck_lastmodify, sp_ck_md5, sp_ck_sha1 = self.__calcFileCheckInformation__(spirv_file)
                # print("Check begin")
                # print(sha1 == ck_sha1)
                # print(md5 == ck_md5)
                # print(size == ck_size)
                # print(lastmodify == ck_lastmodify)
                # print(sp_ck_sha1 == spirv_sha1)
                # print(sp_ck_size == spirv_size)
                # print(sp_ck_lastmodify == spirv_lastmodify)
                # print(sp_ck_md5 == spirv_md5)
                # print("Check End")
                if (sha1 == ck_sha1) and (md5 == ck_md5) and (lastmodify == ck_lastmodify) \
                        and (sp_ck_lastmodify == spirv_lastmodify) and (sp_ck_md5 == spirv_md5) \
                        and (sp_ck_sha1 == spirv_sha1) :
                    obj.setSpirvFile(spirv_file)
                    obj.setSpirvCacheFile('')
                    # print("Cache Match: ", len(obj.getSpirvFile()))
                else :
                    obj.setSpirvFile('')
                    obj.setSpirvCacheFile(cache_path)

    def __writeShaderFileConfigInformation__(self,section,shader,spirv):
        if not self.configParser.has_section(section):
            self.configParser.add_section(section)
        ck_size, ck_lastmodify, ck_md5, ck_sha1 = self.__calcFileCheckInformation__(shader)
        self.configParser.set(section,'sha1',ck_sha1)
        self.configParser.set(section,'md5',ck_md5)
        self.configParser.set(section, 'size', ck_size)
        self.configParser.set(section, 'lastmodify', ck_lastmodify)
        self.configParser.set(section, 'spirv_file', spirv)

        ck_size, ck_lastmodify, ck_md5, ck_sha1 = self.__calcFileCheckInformation__(spirv)
        self.configParser.set(section, 'spirv_size', ck_size)
        self.configParser.set(section, 'spirv_sha1', ck_sha1)
        self.configParser.set(section, 'spirv_md5', ck_md5)
        self.configParser.set(section, 'spirv_lastmodify', ck_lastmodify)

    def updateShaderCache(self,objs):
        if not self.use_cache :
            return

        write = False

        # update self
        sh_section = self.scriptName
        if not self.configParser.has_section(sh_section):
            self.configParser.add_section(sh_section)
        sc_size, lastmodify, sc_md5, sc_sha1 = self.__calcFileCheckInformation__(sh_section)
        if (sc_size != self.size) or (lastmodify != self.lastmodify) or (sc_md5 != self.md5) or (sc_sha1 != self.sha1) :
            self.configParser.set(sh_section, 'sha1', sc_sha1)
            self.configParser.set(sh_section, 'md5', sc_md5)
            self.configParser.set(sh_section, 'size', sc_size)
            self.configParser.set(sh_section, 'lastmodify', lastmodify)
            write = True

        for obj in objs:
            section = obj.getShaderFile()
            shader = section
            if obj.isRefFile() :
                shader = obj.getRawRefFile()
            spirv_file = obj.getSpirvCacheFile()
            if len(spirv_file) > 0 :
                self.__writeShaderFileConfigInformation__(section,shader,spirv_file)
            write = True

        if write :
            with open(self.configFile, 'w') as cfg:
                self.configParser.write(cfg)

    def __init__(self,use):
        self.root_dir = '.cache'
        self.shader_dir = 'shader'
        self.cache_dir = 'cache'
        self.configFile = os.path.join(self.root_dir, self.shader_dir,'config') # config path
        self.configParser = configparser.ConfigParser()
        self.configParser.read(self.configFile)

        self.scriptName = os.path.basename(__file__) # makeshader.py
        self.cache_valid = False # bool, is cache valid
        self.config_sha1 = '' # sha1 for '.cache/shader/config' ,check if  '.cache/shader/config' is changed
        self.use_cache = use

        self.sha1 = '' # string, self sha1
        self.md5 = '' # string, self md5
        self.size = '' # number, self size
        self.lastmodify = '' # string, self lastmodify


def genShaderFileObjs(shaders, macros):
    shaderObjs = []
    print(macros)
    for fileName in shaders:
        obj = ShaderFile(shader=fileName, ref=False, raw=None)
        shaderObjs.append(obj)
        simplename = fileName.split('/')
        simplename = simplename[len(simplename)-1]

        if simplename in macros:
            for macro in macros[simplename]:
                newName = fileName.replace(".comp", "") + "_" + macro + ".comp"
                obj = ShaderFile(shader=newName, ref=True, raw=fileName)
                obj.setMacro(macro)
                shaderObjs.append(obj)
    return shaderObjs


def genJsonHeadFile():
    writeHeadFile = False
    with open("glsl/headfile.json") as f:
        originShaders = json.loads(f.read())
        for s in shaders:
            if not s in originShaders:
                print("Write Head File")
                writeHeadFile = True
                break
    if (writeHeadFile):
        allShaders = {}
        for s in shaders:
            allShaders[s] = "glsl"
        with open("glsl/headfile.json", "w") as f:
            f.write(json.dumps(allShaders, indent=4))


def genRefCompFiles(objs):
    for obj in objs:
        if obj.isRefFile():
            raw = obj.getRawRefFile()
            dst = obj.getShaderFile()
            if len(raw) > 0 and len(dst) > 0:
                with open(raw) as f:
                    contents = f.read().split('\n')
                    content = contents[0] + "\n" + "#define " + obj.getMacro() + "\n"
                    for i in range(1, len(contents)):
                        content += contents[i] + "\n"
                    with open(dst, 'w') as wf:
                        wf.write(content)

def removeRefCompFiles(objs):
    for obj in objs:
        if obj.isRefFile():
            s = obj.getShaderFile()
            if os.path.exists(s) and os.path.isfile(s):
                os.remove(s)

def genMapFile(objs):
    mapFile = "VulkanShaderMap.cpp"
    cpp = '/*Auto Generated File, Don\' Modified.*/\n'
    cpp += "#include \"VulkanShaderMap.hpp\"\n"
    cpp += "#include \"AllShader.h\"\n"
    cpp += 'namespace MNN {\n'
    cpp += 'void VulkanShaderMap::init() {\n'
    for obj in objs:
        name = obj.getFileName()
        cpp += 'mMaps.insert(std::make_pair(\"'+ name + '", std::make_pair(' + name + ',' + name + '_len' ')));\n'
    cpp += '}\n'
    cpp += '}\n'
    with open(mapFile, 'w') as f:
        f.write(cpp)

def genCppFile(objs, inc, dst):
    cpp = "#include \"" + inc + "\"\n"
    genRefCompFiles(objs)
    for obj in objs:
        s = obj.getShaderFile()
        name = obj.getFileName()
        #print name
        out = 'tempspv'
        rm = True
        spirv_cache = obj.getSpirvFile()
        # print("cache:", len(spirv_cache))
        if len(spirv_cache) <= 0 :
            spirv_save = obj.getSpirvCacheFile()
            if len(spirv_save) > 0:
                out = spirv_save
                rm = False
            print(os.popen("glslangValidator -V " + s + " -Os -o " + out).read())
        else:
            out = spirv_cache
            rm = False
        cpp_tmp_file = 'temp.spv.cpp'
        os.popen("xxd -i "+ out +" > " + cpp_tmp_file).read()
        with open(cpp_tmp_file) as f:
            rep = out.replace(os.sep,'_')
            rep = rep.replace('.','_')
            allContent = f.read().replace(rep, name)
            cpp += 'const ' + allContent + '\n'
        if os.path.exists(cpp_tmp_file) and os.path.isfile(cpp_tmp_file) :
            os.remove(cpp_tmp_file)
        if rm and os.path.exists(out) and os.path.isfile(out) :
            os.remove(out)

    with open(dst, "w") as f:
        f.write(cpp)

    removeRefCompFiles(objs)


def genHppFile(objs, fileName):
    h = "#ifndef VK_GLSL_SHADER_AUTO_GENERATE_H\n#define VK_GLSL_SHADER_AUTO_GENERATE_H\n"
    for obj in objs:
        name = obj.getFileName()
        print(name)
        h += "extern const unsigned char " + name + "[];\n";
        h += 'extern unsigned int ' + name + '_len;\n'
    h += "#endif"
    with open(fileName, "w") as f:
        f.write(h)


def generateFile(headfile, sourcefile, shaders, macros, cache):
    #genJsonHeadFile()
    print(macros)
    fileObjs = genShaderFileObjs(shaders, macros)
    cache.setupShaderCache(fileObjs)
    genHppFile(fileObjs, headfile)
    genCppFile(fileObjs, headfile, sourcefile)
    cache.updateShaderCache(fileObjs)
    genMapFile(fileObjs)



def parseArgs(argv):
    try:
        opts, args = getopt.getopt(argv, "hf", ["force="])
    except getopt.GetoptError:
        print('makeshader.py [-h,-f]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('makeshader.py [-h,-f,--force] <-h> help <-f,--force> disable cache')
            sys.exit()
        elif opt in ("-f", "--force"):
            return False
    return True


if __name__ == '__main__':
    use_cache = parseArgs(sys.argv[1:])

    shaderCache = ShaderCache(use_cache)
    if use_cache :
        if not shaderCache.initlizateShaderCache() :
            print("cache init failed,do't use cache")

    shaders = findAllShader(gDefaultPath)
    jsonFile = open(gDefaultPath +'/macro.json', 'r')
    macros = json.loads(jsonFile.read())
    jsonFile.close()
    generateFile(gOutputHeadFile, gOutputSourceFile, shaders, macros, shaderCache)
    # generateFileAsm("AllShader_asm.h", "AllShader_asm.cpp", "spirv");
