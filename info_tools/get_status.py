### TODOs & Things to Think About ###
# Argparse?
# Refactor menu_launcher to import this file
# plugin status needs to be moved here
# This needs to be called with some x args and needs to redirect to get status
# Everything that depends on plugin status or some function involved will need to me moved here -> will break other calls -> need to find and figure out how to redirect here
# How do those calls go to the specific subfunction that was going to be used???
# What other imports do I need to make sure none of the functions break: os, subprocess, check_output, ConfigParser
# How to deal with PathDirs()?
# Tests will break

# Step 1 - Bring the plugins status stuff into this file (might have to rework plugin status to separate menu dict from regular lists/dicts for API)

import ConfigParser

import os
import sys

from subprocess import call, check_output, PIPE, Popen

class PathDirs:
    """ Global path directories for parsing templates """
    def __init__(self,
                 base_dir="/var/lib/docker/data/",
                 collectors_dir="collectors",
                 core_dir="core",
                 plugins_dir="plugins/",
                 plugin_repos="plugin_repos",
                 template_dir="templates/",
                 vis_dir="visualization",
                 info_dir="/data/info_tools/",
                 data_dir="/data/"
                 ):
        self.base_dir = base_dir
        self.collectors_dir = base_dir + collectors_dir
        self.core_dir = base_dir + core_dir
        self.plugins_dir = base_dir + plugins_dir
        self.plugin_repos = base_dir + plugin_repos
        self.template_dir = base_dir + template_dir
        self.vis_dir = base_dir + vis_dir
        self.info_dir = info_dir
        self.data_dir = data_dir

# Parses modes.template and returns a dict containing all specifically enabled containers
# Returns dict along the format of: {'namespace': ["all"], 'namespace2': [""], 'namespace3': ["plug1", "plug2"]}
def get_mode_config(path_dirs):
    # Parsing modes.template
    modes = {}
    try:
        config = ConfigParser.RawConfigParser()
        # needed to preserve case sensitive options
        config.optionxform=str
        config.read(path_dirs.template_dir+'modes.template')
        # Check if any runtime configurations
        if config.has_section("plugins"):
            plugin_array = config.options("plugins")
            # Check if there are any options
            if plugin_array:
                for plug in plugin_array:
                    modes[plug] = config.get("plugins", plug).replace(" ", "").split(",")
        # If not then there are no special runtime configurations and modes is empty
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_mode_config")
        pass

    return modes

# Parses core.template to get all runtime configurations for enabling/disabling cores
# Returns dict along the format of: {'passive': "on", 'active': "on", 'aaa-redis': "off"}
def get_core_config(path_dirs):
    # Parsing core.template
    cores = {}
    try:
        config = ConfigParser.RawConfigParser()
        # needed to preserve case sensitive options
        config.optionxform=str
        config.read(path_dirs.template_dir+'core.template')
        passive = None
        active = None
        # Check if any run-time configurations for core-collectors
        if config.has_section("local-collection"):
            # Check for passive collector configs
            if config.has_option("local-collection", "passive"):
                passive = config.get("local-collection", "passive").replace(" ", "")
            # Check for active collector configs
            if config.has_option("local-collection", "active"):
                active = config.get("local-collection", "active").replace(" ", "")
            if passive in ["on", "off"]:
                cores['passive'] = passive
            if active in ["on", "off"]:
                cores['active'] = active
        # If not then everything is enabled and cores is empty

        # Check if any run-time configurations for core
        if config.has_section("locally-active"):
            active_array = config.options("locally-active")
            # Check if there are any options
            if active_array:
                for option in active_array:
                    cores[option] = config.get("locally-active", option).replace(" ", "")
        # If not then everything is enabled and cores is empty
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_core_config")
        pass

    return cores

# Retrieves installed cores
# Returns list: ["core1", "core2", "core3"]
def get_installed_cores(path_dirs):
    cores = []
    try:
        # Get all cores
        cores = [ core for core in os.listdir(path_dirs.core_dir) if os.path.isdir(os.path.join(path_dirs.core_dir, core)) ]
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_installed_cores")
        pass

    return cores

# Retrieves installed collectors by category: active, passive, or both (all)
# Returns list: ["coll1", "coll2", "coll3"]
def get_installed_collectors(path_dirs, c_type):
    colls = []
    try:
        # Get all collectors
        collectors = [ collector for collector in os.listdir(path_dirs.collectors_dir) if os.path.isdir(os.path.join(path_dirs.collectors_dir, collector)) ]

        # Filter by passive/active/all
        if c_type == "passive":
            colls = [ collector for collector in collectors if "passive-" in collector ]
        elif c_type == "active":
            colls = [ collector for collector in collectors if "active-" in collector ]
        elif c_type == "all":
            colls = collectors
        else:
            with open("/tmp/error.log", "a+") as myfile:
                myfile.write("Error in get_installed_collectors\n" + "Invalid collector parameter: " + str(c_type))
            myfile.close()
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_installed_collectors")
        pass

    return colls

# Retrieves installed visualizations
# Returns list: ["vis1", "vis2", "vis3"]
def get_installed_vis(path_dirs):
    vis = []
    try:
        # Get all visualizations
        vis = [ visualization for visualization in os.listdir(path_dirs.vis_dir) if os.path.isdir(os.path.join(path_dirs.vis_dir, visualization)) ]
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_installed_vis")
        pass

    return vis

# Retrieves all plugins by namespace; e.g. - features/tcpdump || features/hexparser
# Note returns a dict of format: {'namespace': [p1, p2, p3, ...], 'namespace2': [p1, p2, p3, ...]}
def get_installed_plugins(path_dirs):
    p = {}
    try:
        # Get all namespaces
        namespaces = [ namespace for namespace in os.listdir(path_dirs.plugins_dir) if os.path.isdir(os.path.join(path_dirs.plugins_dir, namespace)) ]

        # For each namespace, retrieve all plugins and index by namespace
        for namespace in namespaces:
            p[namespace] = [ plugin for plugin in os.listdir(path_dirs.plugins_dir+namespace) if os.path.isdir(os.path.join(path_dirs.plugins_dir+namespace, plugin)) ]
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_installed_plugins")
        pass

    return p

def get_all_installed(path_dirs):
    """
    Returns all installed containers as a dict, and each subset separately.
    {'cores':["core1", "core2"], 'collectors':["coll1", "coll2"]}
    """
    all_installed = {}
    list_installed = {}
    try:
        # Get each set of containers by type
        all_cores = get_installed_cores(path_dirs)
        all_colls = get_installed_collectors(path_dirs, "all")
        all_vis = get_installed_vis(path_dirs)

        # Note - Dictionary
        all_plugins = get_installed_plugins(path_dirs)

        all_installed['core'] = all_cores
        all_installed['collectors'] = all_colls
        all_installed['visualization'] = all_vis

        # Check if all_plugins is empty
        if all_plugins:
            all_installed.update(all_plugins)
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_all_installed")
        pass

    return all_installed, all_cores, all_colls, all_vis, all_plugins

def get_mode_enabled(path_dirs, mode_config):
    """ Returns all images enabled from modes.template """
    mode_enabled = {}
    try:
        all_installed, all_cores, all_colls, all_vis, all_plugins = get_all_installed(path_dirs)

        # if mode_config is empty, no special runtime configuration
        if not mode_config:
            mode_enabled = all_installed
        # mode_config has special runtime configs
        else:
            # Containers by Category
            core_enabled = []
            coll_enabled = []
            vis_enabled = []

            # check if core has a specification in mode_config
            if "core" in mode_config.keys():
                val = mode_config['core']
                # val is either: ["all"] or ["none"]/[""] or ["core1", "core2", etc...]
                if val == ["all"]:
                    core_enabled = all_cores
                elif val in [["none"], [""]]:
                    core_enabled = []
                else:
                    core_enabled = val
            # if not, then no runtime config for core, use all
            else:
                core_enabled = all_cores

            # check if collectors has a specification in mode_config
            if "collectors" in mode_config.keys():
                val = mode_config['collectors']
                # val is either: ["all"] or ["none"]/[""] or ["coll1", "coll2", etc...]
                if val == ["all"]:
                    coll_enabled = all_colls
                elif val in [["none"], [""]]:
                    coll_enabled = []
                else:
                    coll_enabled = val
            # if not, then no runtime config for coll, use all
            else:
                coll_enabled = all_colls

            # check if visualizations has a specification in mode_config
            if "visualization" in mode_config.keys():
                val = mode_config['visualization']
                # val is either: ["all"] or ["none"]/[""] or ["coll1", "coll2", etc...]
                if val == ["all"]:
                    vis_enabled = all_vis
                elif val in [["none"], [""]]:
                    vis_enabled = []
                else:
                    vis_enabled = val
            # if not, then no runtime config for vis, use all
            else:
                vis_enabled = all_vis

            # plugins
            for namespace in mode_config.keys():
                if namespace not in ["visualization", "collectors", "core"]:
                    val = mode_config[namespace]
                    # val is either: ["all"] or ["none"]/[""] or ["some", "some2", etc...]
                    if val == ["all"]:
                        if namespace in all_plugins:
                            mode_enabled[namespace] = all_plugins[namespace]
                    elif val in [["none"], [""]]:
                        mode_enabled[namespace] = []
                    else:
                        mode_enabled[namespace] = val

            # if certain plugin namespaces have been omitted from the modes.template file
            # then no special runtime config and use all
            for namespace in all_plugins:
                if namespace not in mode_enabled:
                    mode_enabled[namespace] = all_plugins[namespace]

            mode_enabled['core'] = core_enabled
            mode_enabled['collectors'] = coll_enabled
            mode_enabled['visualization'] = vis_enabled
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_mode_enabled")
        pass

    return mode_enabled

def get_core_enabled(path_dirs, core_config):
    """ Returns all enabled and disabled images from core.template """
    core_enabled = {}
    core_disabled = {}
    try:
        passive_colls = get_installed_collectors(path_dirs, "passive")
        active_colls = get_installed_collectors(path_dirs, "active")
        coll_enabled = []
        coll_disabled = []
        # only if not empty
        if core_config:
            ### Local-Collection ###
            # Check passive/active settings
            # Default all on
            p_colls = passive_colls
            a_colls = active_colls

            if 'passive' in core_config.keys() and core_config['passive'] == "off":
                    p_colls = []
            if 'active' in core_config.keys() and core_config['active'] == "off":
                    a_colls = []

            # Add all passively enabled collectors
            if p_colls:
                coll_enabled = coll_enabled + p_colls
            else:
                coll_disabled = coll_disabled + passive_colls
            # Add all actively enabled collectors
            if a_colls:
                coll_enabled = coll_enabled + a_colls
            else:
                coll_disabled = coll_disabled + active_colls

            ### Locally-Active ###
            # Check locally-active settings
            # Get all keys (containers) that are turned off
            locally_disabled = [ key for key in core_config if key not in ['passive', 'active'] and core_config[key] == "off" ]
            # Get all keys (containers) that are turned on
            locally_enabled = [ key for key in core_config if key not in ['passive', 'active'] and core_config[key] == "on" ]

            core_enabled['collectors'] = coll_enabled
            core_enabled['core'] = locally_enabled
            core_disabled['collectors'] = coll_disabled
            core_disabled['core'] = locally_disabled
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_core_enabled")
        pass

    return core_enabled, core_disabled

def get_enabled(path_dirs):
    """ Returns containers that have been enabled/disabled by config """
    enabled = {}
    disabled = []
    try:
        # Retrieve configuration enablings/disablings for all containers
        mode_config = get_mode_config(path_dirs)
        core_config = get_core_config(path_dirs)

        # Retrieve containers enabled by mode
        # Note - mode_enabled and its complement form the complete set of containers
        mode_enabled = get_mode_enabled(path_dirs, mode_config)

        # Retrieve containers enabled/disabled by core
        # Note - the union of core_enabled and core_disabled DO NOT form the complete set of containers
        core_enabled, core_disabled = get_core_enabled(path_dirs, core_config)

        # The complete set of containers
        all_installed = get_all_installed(path_dirs)[0]

        ### Intersection Logic by Case: ###
        # Case 1: container is in mode_enabled and in core_enabled -> enabled
        # Case 2: container is in mode_enabled and in core_disabled-> disabled
        # Case 3: container is not in mode_enabled and in core_enabled -> disabled
        # Case 4: container is not in mode_enabled and not in core_enabled -> disabled
        # Case 5: container is in mode_enabled and not in core_enabled or disabled -> enabled
        # Case 6: container is not in mode_enabled and not in core_enabled or disabled -> disabled
        # Case 7: None of the other cases -> Something went grievously wrong...

        # Get keys from all_installed, and initialize values to empty list
        all_enabled = {}
        all_disabled = {}
        for namespace in all_installed:
            all_enabled[namespace] = []
            all_disabled[namespace] = []

        for namespace in all_installed.keys():
            # For 'cores' & 'collectors'
            if namespace in mode_enabled.keys() and namespace in core_enabled.keys():
                for container in all_installed[namespace]:
                        # Case 1
                        if container in mode_enabled[namespace] and container in core_enabled[namespace]:
                            all_enabled[namespace].append(container)
                        # Case 2
                        elif container in mode_enabled[namespace] and container in core_disabled[namespace]:
                            all_disabled[namespace].append(container)
                        # Case 3
                        elif container not in mode_enabled[namespace] and container in core_enabled[namespace]:
                            all_disabled[namespace].append(container)
                        # Case 4
                        elif container not in mode_enabled[namespace] and container in core_disabled[namespace]:
                            all_disabled[namespace].append(container)
                        # Case 5
                        elif container in mode_enabled[namespace]:
                            all_enabled[namespace].append(container)
                        # Case 6
                        elif container not in mode_enabled[namespace]:
                            all_disabled[namespace].append(container)
                        # Case 7
                        else:
                            with open("/tmp/error.log", "a+") as myfile:
                                myfile.write("get_enabled error: Case 7 reached!\n")
            else:
            # For 'visualizations' & all plugin namespaces
                for container in all_installed[namespace]:
                    if namespace in mode_enabled:
                        # Case 5
                        if container in mode_enabled[namespace]:
                            all_enabled[namespace].append(container)
                        # Case 6
                        elif container not in mode_enabled[namespace]:
                            all_disabled[namespace].append(container)
                        # Case 7
                        else:
                            with open("/tmp/error.log", "a+") as myfile:
                                myfile.write("get_enabled error: Case 7 reached!\n")

        enabled = all_enabled
        disabled = all_disabled
    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_enabled")
        pass

    return enabled, disabled

def get_plugin_status(path_dirs):
    """ Displays status of all running, not running/built, not built, and disabled plugins """
    plugins = ()

    try:
        ### Get All Installed Images (By Filewalk) ###
        all_installed, all_cores, all_colls, all_vis, all_plugins = get_all_installed(path_dirs)

        ### Get Enabled/Disabled Images ###
        # Retrieves all enabled images
        enabled, disabled = get_enabled(path_dirs)

        # Make a list of disabled images of format: namespace/image
        disabled_images = []

        for namespace in disabled:
            for image in disabled[namespace]:
                disabled_images.append(namespace+'/'+image)

        ### Get Disabled Containers ###
        # Need to cross reference with all installed containers to determine all disabled containers
        disabled_containers = []

        containers = check_output(" docker ps -a | grep '/' | awk \"{print \$NF}\" ", shell=True).split("\n")
        containers = [ container for container in containers if container != "" ]

        # Intersect the set of all containers with the set of all disabled images
        # Images form the basis for a container (in name especially), but there can be multiple containers per image
        for container in containers:
            for namespace in disabled:
                for image in disabled[namespace]:
                    if image in container:
                        disabled_containers.append(container)

        ### Get all Running Containers, not including disabled containers ###
        # Retrieves running or restarting docker containers and returns a list of container names
        running = check_output(" { docker ps -af status=running & docker ps -af status=restarting; } | grep '/' | awk \"{print \$NF}\" ", shell=True).split("\n")
        running = [ container for container in running if container != "" ]

        # Running containers should not intersect with disabled containers/images.
        # Containers should not exist/be running if disabled
        running_errors = [ container for container in running if container in disabled_containers ]
        running = [ container for container in running if container not in disabled_containers ]

        ### Get all NR Containers, not including disabled containers ###
        # Retrieves docker containers with status exited, paused, dead, created; returns as a list of container names
        nrcontainers = check_output(" { docker ps -af status=created & docker ps -af status=exited & docker ps -af status=paused & docker ps -af status=dead; } | grep '/' | awk \"{print \$NF}\" ", shell=True).split("\n")
        nrcontainers = [ container for container in nrcontainers if container != "" ]
        # Containers should not exist if disabled
        nr_errors = [ container for container in nrcontainers if container in disabled_containers ]
        nrbuilt = [ container for container in nrcontainers if container not in disabled_containers ]

        ### Get all Built Images, not including disabled images ###
        # Retrieve all built docker images
        built = check_output(" docker images | grep '/' | awk \"{print \$1}\" ", shell=True).split("\n")
        built = [ image for image in built if image != "" ]
        # Image *should* be removed if disabled
        built_errors = [ image for image in built if image in disabled_images ]

        ### Get all Not Built Images, not including disabled images ###
        # If image hasn't been disabled and isn't present in docker images then add
        notbuilt = []
        for namespace in all_installed:
            for image in all_installed[namespace]:
                if namespace in disabled and image not in disabled[namespace] and namespace+'/'+image not in built:
                    notbuilt.append(namespace+'/'+image)

        plugins = (running, nrbuilt, built, disabled_containers, disabled_images, notbuilt, running_errors, nr_errors, built_errors)

    except Exception as e:
        with open('/tmp/refactor.log', 'a+') as myfile:
            myfile.write("Error - get_plugin_status")
        pass

    return plugins

def main(base_dir=None, info_dir=None, data_dir=None):
    path_dirs = PathDirs()
    if base_dir:
        path_dirs = PathDirs(base_dir=base_dir)
    if info_dir:
        path_dirs.info_dir = info_dir
    if data_dir:
        path_dirs.data_dir = data_dir

    plugins = get_plugin_status(path_dirs)
    print plugins

if __name__ == "__main__":
    try:
        if len(sys.argv) == 4:
            main(base_dir=sys.argv[1], info_dir=sys.argv[2], data_dir=sys.argv[3])
        else:
            main()
    except Exception as e:
        pass
