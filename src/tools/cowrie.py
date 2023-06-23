# External
import os
from string import Template

# Internal
from common.utils.files import *
from common.utils.logs import *
from common.utils.system import *
from common.utils.misc import *
import common.utils.settings as settings
import glob

class CowrieController:
	def __init__(self):
		log(INFO, "CowrieController.__init__: creating the CowrieController")
		self.run_dir       = to_root_path("run/cowrie/")
		self.pid_file      = to_root_path(self.run_dir+"/cowrie.pid")
		self.log_file      = to_root_path(self.run_dir+"/cowrie.log")
		self.json_file     = to_root_path(self.run_dir+"/cowrie.json")
		self.conf_file     = to_root_path(self.run_dir+"/cowrie.conf")
		self.download_path = to_root_path(self.run_dir+"/download/")

		self.conf_template  = ""
		self.start_template = ""

		with open(to_root_path("var/template/cowrie_conf.txt"), "r") as temp_file:
			self.conf_template = Template(temp_file.read())
		with open(to_root_path("var/template/start_cowrie.txt"), "r") as temp_file:
			self.start_template = Template(temp_file.read())

	def __del__(self):
		pass

	def configure(self, honeypot, hpfeeds, settings):
		# Settings
		COWRIE_SSH_LISTEN_PORT  = settings["cowrie"]["ssh_listen_port"]
		COWRIE_BACKEND_SSH_HOST = settings["cowrie"]["backend_ssh_host"]
		COWRIE_BACKEND_SSH_PORT = settings["cowrie"]["backend_ssh_port"]
		SOCKET_PORTS            = settings["cowrie"]["socket_ports"]

		# Deleting former configuration
		delete_file(self.conf_file)

		cred  = honeypot["credentials"]
		ident = honeypot["id"]

		params = {
			'download_path'      : self.download_path,
			'listen_port'        : COWRIE_SSH_LISTEN_PORT,
			'backend_host'       : COWRIE_BACKEND_SSH_HOST, #"127.0.0.1"
			'backend_port'       : COWRIE_BACKEND_SSH_PORT+ident, #2000+i
			'backend_user'       : cred["user"],
			'backend_pass'       : cred["pass"],
			'hpfeeds_server'     : hpfeeds["server"],
			'hpfeeds_port'       : hpfeeds["port"],
			'hpfeeds_identifier' : hpfeeds["identifier"],
			'hpfeeds_secret'     : hpfeeds["secret"],
			'logfile'            : self.json_file,
			'socket_port'        : SOCKET_PORTS+ident
		}

		content = self.conf_template.substitute(params)
		
		with open(self.conf_file, "w") as configuration_file:
			configuration_file.write(content)

	# Prepare cowrie to run
	def prepare(self):
		# Delete previous pid file
		delete(to_root_path("run/cowrie/"), suffix=".pid")

		# Allow cowrie user to access cowrie files
		run("chown -R cowrie "+to_root_path("run/cowrie/"))

	def start(self):
		if self.is_running(): self.stop()

		self.prepare()

		cmd = self.start_template.substitute({
			"conf_path" : self.conf_file,
			"pid_path"  : self.pid_file,
			"log_path"  : self.log_file
		})

		if not run(cmd):
			log(ERROR, "CowrieController.start: failed")

	def stop(self):
		try:
			kill_from_file(os.path.join(path, pidpath))
		except:
			log(WARNING, "Failed to stop a cowrie instance. The pid file is: "+str(pidpath))
			return False
		else:
			return True

	def is_running(self):
		return read_pid_file(to_root_path("run/cowrie/cowrie.pid")) is not None