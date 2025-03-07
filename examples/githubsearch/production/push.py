# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import traceback
import sys
import time
import urllib.request, urllib.error, urllib.parse
import os
import shutil
import signal
import runServer

sys.path.insert(0, '..')
import localconstants

# where to install ui files in prod, relative to ~:
UI_PATH = 'src/github-ui'

def run(cmd):
  if os.system(cmd):
    raise RuntimeError('%s failed; cwd=%s' % (cmd, os.getcwd()))

if len(sys.argv) == 1:
  doServer = True
  doUI = True
  doReindex = False
else:
  doServer = False
  doUI = False
  doReindex = False

  for arg in sys.argv[1:]:
    if arg == '-ui':
      doUI = True
    elif arg == '-server':
      doServer = True
    elif arg == '-reindex':
      doReindex = True
    else:
      raise RuntimeError('unknown arg %s' % arg)

#userHost = 'changingbits@web504.webfaction.com'
userHost = 'ec2-user@githubsearch.mikemccandless.com'
#userHost = 'mike@10.17.4.12'
sshIdent = ''
#sshIdent = '-i /home/mike/.ssh/aws_changingbits.pem'

print()

# nocommit put back
if False:
  print('Snapshot')
  run(f'ssh -t {sshIdent} {userHost} "cd {UI_PATH}/production; python3 -u snapshot.py"')

if doServer:
  serverDistPath = '/l/luceneserver/build/luceneserver-%s-SNAPSHOT.zip' % localconstants.LUCENE_SERVER_VERSION
  print()
  print(f'copy {serverDistPath}"')
  run(f'scp {sshIdent} {serverDistPath} {userHost}:{UI_PATH}')
  run(f'ssh {sshIdent} {userHost} "cd {UI_PATH}; rm -f luceneserver; unzip luceneserver-{localconstants.LUCENE_SERVER_VERSION}-SNAPSHOT.zip; ln -s luceneserver-{localconstants.LUCENE_SERVER_VERSION}-SNAPSHOT luceneserver; rm luceneserver-{localconstants.LUCENE_SERVER_VERSION}-SNAPSHOT.zip"')

if doUI:
  print('Push UI/indexing scripts')
  run(f'scp {sshIdent} -r ../gitHistory.py ../handle.py ../index_github.py ../Latin-dont-break-issues.rbbi ../server.py ../moreFacets.py ../search.py ../static ../production ../suggest.py ../local_db.py ../util.py ../direct_load_all_github_issues.py ../update_from_github.py {userHost}:{UI_PATH}')

if doReindex:
  extra = ' -reindex'
else:
  extra = ''

print(f'\nnow restart')
run(f'ssh -t {sshIdent} {userHost} "cd {UI_PATH}/production; python3 -u restart.py{extra}"')

print()
print('Verify')
while True:
  try:
    s = urllib.request.urlopen('http://jirasearch.mikemccandless.com/search.py').read().decode('utf-8')
  except:
    print()
    print('Failed to load search.py... will retry:')
    traceback.print_exc()
  else:
    if s.find('<b>Updated</b>') != -1:
      print('  success!')
      break
    elif s.find('isn\'t started: cannot search'):
      time.sleep(0.5)
    else:
      print('GOT %s' % s)
      raise RuntimeError('server is not working?')
