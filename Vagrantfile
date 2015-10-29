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
                    d.name = vm_name
                end
            end
        end
    end
end