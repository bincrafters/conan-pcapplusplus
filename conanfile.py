from conans import ConanFile, tools, MSBuild, AutoToolsBuildEnvironment
import os


class PcapplusplusConan(ConanFile):
    name = "pcapplusplus"
    version = "18.08"
    license = "Unilicense"
    url = "https://github.com/AndreyBronin/conan-PcapPlusPlus"
    description = "Conan package for PcapPlusPlus"
    homepage = "https://github.com/seladb/PcapPlusPlus"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "immediate-mode": [True, False]
    }
    default_options = "immediate-mode=False"
    generators = "make"

    def requirements(self):
        if self.settings.os == "Windows":
            self.requires.add("winpcap/4.1.3@bincrafters/stable")
            if self.settings.compiler == "Visual Studio":
                self.requires.add("pthread-win32/2.9.1@bincrafters/stable")
        else:
            self.requires.add("libpcap/1.8.1@bincrafters/stable")

    def source(self):
        self.run("git clone --branch v18.08 --depth 1 https://github.com/seladb/PcapPlusPlus.git")

    #def config_options(self):
        #if self.settings.os == "Windows":
        #    del self.options.immediate-mode

    def build(self):
        with tools.chdir("PcapPlusPlus"):
            if self.settings.os == "Linux":
                config_command = ("./configure-linux.sh --default --install-dir %s" % self.package_folder)
                if self.option.immediate-mode:
                    command += " --use-immediate-mode"
                # libpcap_info = self.deps_cpp_info["libpcap"]
                # include_path = libpcap_info.include_paths[0]
                # lib_path = libpcap_info.lib_paths[0]
                self.run(command)
            elif self.settings.os == "Macos":
                config_command = ("./configure-mac_os_x.sh --install-dir %s" % self.package_folder)
                if self.option.immediate-mode:
                    command += " --use-immediate-mode"
                # libpcap_info = self.deps_cpp_info["libpcap"]
                # include_path = libpcap_info.include_paths[0]
                # lib_path = libpcap_info.lib_paths[0]
                self.run(command)
            elif self.settings.os == "Windows":
                winpcap_path = self.deps_cpp_info["winpcap"].rootpath 
                if self.settings.compiler == "gcc": # mingw compiler
                    self.run("configure-windows-mingw.bat mingw-w64 --mingw-home %s --msys-home %s --winpcap-home %s" % (os.getenv("MINGW_HOME"), os.getenv("MSYS_ROOT"), winpcap_path))
                else: # visual studio compiler
                    pthreads_path = self.deps_cpp_info["pthread-win32"].rootpath
                    self.run("configure-windows-visual-studio.bat --winpcap-home %s --pthreads-home %s" % (winpcap_path, pthreads_path))
            else:
                raise ConanException("%s is not supported" % self.settings.os)

            # build_flags = '-I%s' % include_path
            # build_flags += ' -L%s' % lib_path
        # self.run("make -e PCAPPP_BUILD_FLAGS='%s' libs -j5" % build_flags)
        if self.settings.compiler == "Visual Studio":
            msbuild = MSBuild(self)
            msbuild.build("mk\vs2015\PcapPlusPlus.sln")
            msbuild.build("mk\vs2015\PcapPlusPlus-Examples.sln")
            msbuild.build("mk\vs2015\Tutorials.sln")
        else:
            with tools.chdir("PcapPlusPlus"):
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make()

    def package(self):
        if self.settings.os == "Windows":
            self.copy("*.h", dst="include", src="PcapPlusPlus\\Dist\\header")
            self.copy("*.lib", dst="lib", src="PcapPlusPlus\\Dist\\", keep_path=False)
            self.copy("*.pdb", dst="lib", src="PcapPlusPlus\\Dist\\", keep_path=False)
            self.copy("*.*", dst="bin", src="PcapPlusPlus\\Dist\\examples", keep_path=False)
        else:
            self.run("make install")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

