# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
Vagrant.require_version ">= 1.6.0"

ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'

require 'yaml'

# Read details of containers to be created from YAML file
# Be sure to edit 'containers.yml' to provide container details
containers = YAML.load_file('containers.yml')

container_data = containers["glusterfs"]["data"]
#server = container_data ["server"]
client = container_data["client"]
web_proxy = container_data["web"]

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    #(1..server["count"]).each do |i|
    #    config.vm.define vm_name = "#{server["name"]}-#{i}" do |config|
    #        config.vm.synced_folder ".", "/vagrant", disabled: true
    #        config.vm.provider "docker" do |d|
    #            config.vm.hostname = vm_name
    #            d.remains_running = true
    #            d.build_dir = server["dir"]
    #            d.build_args = ["--tag=farmatholin/glusterfs-server:latest"]
    #            d.privileged = true
    #            d.name = vm_name
    #            d.volumes = ["/#{containers["gluster"]["gluster_brick"]}_#{i}:/#{containers["gluster"]["gluster_brick"]}"]
    #        end
    #    end
    #end
    config.vm.define "web" do |web|
        web.vm.synced_folder ".", "/vagrant", disabled: true
        web.vm.provider "docker" do |d|
            d.privileged = true
            d.remains_running = true
            d.image = client["image"]
            #d.build_dir = client["dir"]
            #d.build_args = ["--tag=farmatholin/glusterfs-client:latest"]
            d.name = client["name"]
            d.expose = [8000]
            d.has_ssh = false
            d.cmd = ["/usr/local/bin/gunicorn", "-w #{client["workers"]}", "-b :8000", "app:app"]
        end
    end
    config.vm.define "nginx" do |nginx|
        nginx.vm.synced_folder ".", "/vagrant", disabled: true
        nginx.vm.provider "docker" do |d|
            #d.build_dir = web_proxy["dir"]
            d.image = web_proxy["image"]
            d.name = web_proxy['name']
            d.ports = ["#{web_proxy["port"]}:80"]
            d.link("#{client["name"]}:#{client["name"]}")
            d.remains_running = true
            d.has_ssh = false
        end
    end
end