# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
Vagrant.require_version ">= 1.6.0"

ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'

require 'yaml'

# Read details of containers to be created from YAML file
# Be sure to edit 'containers.yml' to provide container details
containers = YAML.load_file('containers.yml')

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    containers["data"].each do |container|
        (1..container["count"]).each do |i|
            config.vm.define vm_name = "#{container["name"]}-#{i}" do |config|
                config.vm.synced_folder ".", "/vagrant", disabled: true
                config.vm.provider "docker" do |d|
                    config.vm.hostname = vm_name
                    d.build_dir = container["dir"]
                    d.privileged = true
                    if container["type"] != 'server'
                        d.name = container["name"]
                        d.expose = [8000]
                        d.cmd = ["/usr/local/bin/gunicorn", "-w 2", "-b :8000", "app:app"]
                    else
                        d.name = vm_name
                        d.volumes = ["/#{containers["gluster"]["gluster_brick"]}_#{i}:/#{containers["gluster"]["gluster_brick"]}"]
                    end
                end
            end
        end
    end
    #config.vm.define "web" do |web|
        #web.vm.synced_folder ".", "/vagrant", disabled: true
        #web.vm.provider "docker" do |d|
            #d.remains_running = true
            #d.build_dir = "client/app"
            #d.name = "web-gluster-client"
            #d.expose = [8000]
            #(1..clients).each do |i|
                #d.link("#{client_name}-#{i}:#{client_name}-#{i}")
            #end
            #d.link("glusterfs-client:glusterfs-client")
            #d.has_ssh = false
            #d.create_args = ["--volumes-from=glusterfs-client"]
            #d.cmd = ["/usr/local/bin/gunicorn", "-w 2", "-b :8000", "app:app"]
       # end
     #end
    config.vm.define "nginx" do |nginx|
        nginx.vm.synced_folder ".", "/vagrant", disabled: true
        nginx.vm.provider "docker" do |d|
            d.build_dir = "client/nginx"
            d.name = "nginx-gluster"
            d.ports = ["9092:80"]
            d.link("glusterfs-client:glusterfs-client")
            d.remains_running = true
            d.has_ssh = false
        end
    end
end