#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from cgnaws import *
from argparse import ArgumentParser
import fileinput
import re, sys, os
from boto import iam

with open("/root/.aws/config") as f:
    for line in f.readlines():
        if line.startswith('aws_access_key_id'):
            aws_access_key_id = line.split()[-1]
        elif line.startswith('aws_secret_access_key'):
            aws_secret_access_key = line.split()[-1]

def get_username():
    iam_connection = iam.connect_to_region("universal", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    return iam_connection.get_user()["get_user_response"]["get_user_result"]["user"]["user_name"]

accounts = { 'wibi' : { 'regions': ['us-west-2'], 'access-key' : aws_access_key_id, 'secret-key' :
    aws_secret_access_key} }

def get_ip(environment):
    connections = establish_connections(accounts)
    reservations = get_reservations(connections)
    instances = get_instances(reservations)
    for i in instances.values()[0]:
        if i._state.name == 'running' and i.tags['Name'] == "bastion."+environment:
            return [j.publicIp for j in i.interfaces if 'publicIp' in j.__dict__.keys()][0]

pattern = re.compile("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|BASTION_IP")

config = """Host *{0}*.aws
IdentityFile /root/.ssh/{1}
User ubuntu
ProxyCommand ssh -i /root/.ssh/private.key {2}@{3} nc $(dig +short %h) %p
UserKnownHostsFile /dev/null
StrictHostKeyChecking no
"""

if __name__ == "__main__":
    with open("/root/.ssh/config", "w") as f:
        for key in (i for i in os.listdir("/root/.ssh/") if i.endswith(".key") and not i.startswith("private")):
            try:
                environment = key.replace('.key','')
                bastion_ip = get_ip(environment)
                print("Bastion IP: "+bastion_ip+" in \""+environment+"\" environment")
                f.write(config.format(environment, key, get_username(), bastion_ip))
            except:
                print("Failed to fetch bastion public IP for \""+environment+"\" environment")
    print "SSH config was successfuly templated"
