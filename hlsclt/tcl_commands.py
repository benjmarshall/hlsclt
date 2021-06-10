def param(name, value):
    return ('%s "%s" ' % (name, value)) if value else ""


def option(name, value):
    return ("%s " % name) if value else ""


def open_project(project_name):
    return "open_project %s" % project_name


def set_top(top_level_function_name):
    return "set_top %s" % top_level_function_name


def add_files(files, cflags='', is_tb=False):
    def add_file(file):
        _cflags = param("-cflags", " ".join((cflags, file.cflags)))
        _tb = option("-tb", is_tb)
        return "add_files %s%s%s" % (_tb, _cflags, file.path)
    return map(add_file, files)


def source(file):
    return "source %s" % file


def open_solution(solution):
    return "open_solution %s" % solution


def set_part(part_name):
    return "set_part %s" % part_name


def create_clock(clock_period):
    return "create_clock -period %s" % clock_period


def csim_design(compiler, clean=True):
    return "csim_design %s-compiler %s" % (option("-clean", clean), compiler)


def cosim_design(language, trace_level=""):
    return ("cosim_design -O %s%s"
            % (param("-rtl", language), (param("-trace_level", trace_level))))


def export_design(format, evaluate=""):
    return ("export_design -format %s %s"
            % (format, param("-evaluate", evaluate)))


def csynth_design():
    return "csynth_design"


def exit():
    return "exit"
