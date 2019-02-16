from conans import ConanFile, tools, MSBuild, AutoToolsBuildEnvironment
import os


class PcapplusplusConan(ConanFile):
    name = "PcapPlusPlus"
    version = "18.08"
    license = "Unilicense"
    description = "PcapPlusPlus is a multiplatform C++ network sniffing and packet parsing and crafting framework"
    topics = ("conan", "pcapplusplus", "pcap", "network", "security", "packet")
    url = "https://github.com/bincrafters/conan-pcapplusplus"
    homepage = "https://github.com/seladb/PcapPlusPlus"
    author = "seladb <pcapplusplus@gmail.com>"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False], 
        "fPIC": [True, False],
        "immediate_mode": [True, False],
    }
    default_options = {
        "shared": False, 
        "fPIC": True,
        "immediate_mode": False,
    }
    generators = "make", "visual_studio"

    _source_subfolder = "PcapPlusPlus"
    
    _sln_file = "mk/vs2015/PcapPlusPlus.sln"

    _vs_projects_to_build =[
        "Common++", 
        "LightPcapNg", 
        "Packet++", 
        "Pcap++", 
    ]

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.immediate_mode
    
    def requirements(self):
        if self.settings.os == 'Windows':
            self.requires("winpcap/4.1.3@bincrafters/stable")
            if self.settings.compiler == "Visual Studio":
                self.requires.add("pthread-win32/2.9.1@bincrafters/stable")
        else:
            self.requires("libpcap/1.8.1@bincrafters/stable")
            
    def source(self):
        tools.get("{0}/archive/v{1}.tar.gz".format(self.homepage, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        with tools.chdir(self._source_subfolder):
            if self.settings.os == "Linux":
                config_command = ("./configure-linux.sh --default")
                if self.options.immediate_mode:
                    config_command += " --use-immediate-mode"
                self.run(config_command)

                libpcap_include_path = self.deps_cpp_info["libpcap"].include_paths[0]
                libpcap_lib_path = self.deps_cpp_info["libpcap"].lib_paths[0]
                libpcap_dirs = "PCAPPP_INCLUDES += -I{0}\nPCAPPP_LIBS_DIR += -L{1}".format(libpcap_include_path, libpcap_lib_path)
                tools.save("mk/PcapPlusPlus.mk", libpcap_dirs, append=True)
                tools.replace_in_file("Pcap++/Makefile", "ifdef LINUX", "ifdef LINUX\nINCLUDES += -I{0}".format(libpcap_include_path))
                    
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make()

            elif self.settings.os == "Macos":
                config_command = ("./configure-mac_os_x.sh")
                if self.options.immediate_mode:
                    config_command += " --use-immediate-mode"
                # libpcap_info = self.deps_cpp_info["libpcap"]
                # include_path = libpcap_info.include_paths[0]
                # lib_path = libpcap_info.lib_paths[0]
                self.run(config_command)
                
                # build_flags = '-I%s' % include_path
                # build_flags += ' -L%s' % lib_path
                # self.run("make -e PCAPPP_BUILD_FLAGS='%s' libs -j5" % build_flags)
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make()

            elif self.settings.os == "Windows":
                if self.settings.compiler != "Visual Studio":
                    raise Exception("Compiler %s is not supported" % self.settings.compiler)

                winpcap_path = self.deps_cpp_info["winpcap"].rootpath 
                pthreads_path = self.deps_cpp_info["pthread-win32"].rootpath
                self.run("configure-windows-visual-studio.bat --winpcap-home %s --pthreads-home %s" % (winpcap_path, pthreads_path))
                self.generate_directory_build_props_file()
                msbuild = MSBuild(self)
                msbuild.build(
                    self._sln_file, 
                    targets=self._vs_projects_to_build,
                    use_env=False, 
                    properties={"WholeProgramOptimization":"None"},
                )
            else:
                raise Exception("%s is not supported" % self.settings.os)

    def package(self):
        self.copy("*.h", dst="include", src="PcapPlusPlus/Dist/header")
        self.copy("*.lib", dst="lib", src="PcapPlusPlus/Dist/", keep_path=False)
        self.copy("*.a", dst="lib", src="PcapPlusPlus/Dist/", keep_path=False)
        self.copy("*.pdb", dst="lib", src="PcapPlusPlus/Dist/", keep_path=False)
        self.copy("*", dst="bin", src="PcapPlusPlus/Dist/examples", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread"])
        if self.settings.os == "Windows":
            self.cpp_info.libs.extend(["Iphlpapi"])

    def generate_directory_build_props_file(self):
    
        log_message = (
            "Generating Directory.Build.Props in the build directory which"
            "injects conan variables into all vcxproj files in the directory tree beneath it. "
            "https://docs.microsoft.com/en-us/visualstudio/msbuild/what-s-new-in-msbuild-15-0"
        )
        
        props_content = r"""<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
    <ImportGroup Label="PropertySheets">
        <Import Project="../conanbuildinfo.props" />
    </ImportGroup>
</Project>
"""
        self.output.warn(log_message)
        tools.save("Directory.Build.props", props_content)
