#!/usr/bin/env python

# Python wrapper for METEOR implementation, by Xinlei Chen
# Acknowledge Michael Denkowski for the generous discussion and help

import os
import sys
import subprocess
import threading
import timeout_decorator

# Assumes meteor-1.5.jar is in the same directory as meteor.py.  Change as needed.
METEOR_JAR = 'meteor-1.5.jar'
# print METEOR_JAR

import os
import fcntl

from multiprocessing.connection import Client
from multiprocessing.connection import Listener

class Meteor:

    def __init__(self):
        self.meteor_cmd = ['java', '-jar', '-Xmx2G', METEOR_JAR, \
                '-', '-', '-stdio', '-l', 'en', '-norm']
        self._create_server()
        # Used to guarantee thread safety
    def _create_server(self):
        self.pid_path = '/tmp/yli-METEOR-pid'
        #self.address = ('localhost', 6000)
        self.address = '/tmp/yli-METEOR-server'
        self.authkey = 'dummy key'
        try:
            pid = open(self.pid_path).read().strip()
            assert 'java' in subprocess.check_output(['ps', '-p', pid, '-o', 'cmd'])
            self.listener = None
            self.meteor_p = None
        except:
            # really create server
            self.meteor_p = subprocess.Popen(self.meteor_cmd, \
                cwd=os.path.dirname(os.path.abspath(__file__)), \
                stdin=subprocess.PIPE, \
                stdout=subprocess.PIPE, \
                stderr=sys.stderr)
            self.pid = self.meteor_p.pid
            open(self.pid_path, 'w').write(str(self.pid))


            if os.fork():
                # put to background
                # the main process should call _compute_score to
                # initialize meteor.jar, which takes longer than 5 seconds
                return
            else:

                while True:
                    if os.path.exists(self.address):
                        os.remove(self.address)

                    listener = Listener(self.address, authkey=self.authkey)
                    try:
                        self._handle_listenser(listener)
                    except:
                        pass
                    finally:
                        listener.close()

    def _handle_listenser(self, listener):

        while True:
            conn = listener.accept()
            try:
                self._handle_conn(conn)
            except:
                pass
            finally:
                conn.close()

    @timeout_decorator.timeout(5)
    def _handle_conn(self, conn):
        print 'accept connection'
        gts = conn.recv()
        res = conn.recv()
        score = self._compute_score(gts, res)
        conn.send(score)

    @timeout_decorator.timeout(5)
    def _handle_client(self, gts, res, conn):
        conn.send(gts)
        conn.send(res)
        score = conn.recv()
        return score

    def compute_score(self, gts, res):
        conn = Client(self.address, authkey=self.authkey)
        try:
            score = self._handle_client(gts, res, conn)
        except:
            score = (0.0, [0.0])
        finally:
            conn.close()
        return score

    def _compute_score(self, gts, res):
        assert(gts.keys() == res.keys())
        imgIds = gts.keys()
        scores = []

        eval_line = 'EVAL'
        for i in imgIds:
            assert(len(res[i]) == 1)
            stat = self._stat(res[i][0], gts[i])
            eval_line += ' ||| {}'.format(stat)

        self.meteor_p.stdin.write('{}\n'.format(eval_line))
        for i in range(0,len(imgIds)):
            scores.append(float(self.meteor_p.stdout.readline().strip()))
        score = float(self.meteor_p.stdout.readline().strip())

        return score, scores

    def method(self):
        return "METEOR"

    def _stat(self, hypothesis_str, reference_list):
        # SCORE ||| reference 1 words ||| reference n words ||| hypothesis words
        hypothesis_str = hypothesis_str.replace('|||','').replace('  ',' ')
        score_line = ' ||| '.join(('SCORE', ' ||| '.join(reference_list), hypothesis_str))
        self.meteor_p.stdin.write('{}\n'.format(score_line))
        return self.meteor_p.stdout.readline().strip()

    def _score(self, hypothesis_str, reference_list):
        # SCORE ||| reference 1 words ||| reference n words ||| hypothesis words
        hypothesis_str = hypothesis_str.replace('|||','').replace('  ',' ')
        score_line = ' ||| '.join(('SCORE', ' ||| '.join(reference_list), hypothesis_str))
        self.meteor_p.stdin.write('{}\n'.format(score_line))
        stats = self.meteor_p.stdout.readline().strip()
        eval_line = 'EVAL ||| {}'.format(stats)
        # EVAL ||| stats
        self.meteor_p.stdin.write('{}\n'.format(eval_line))
        score = float(self.meteor_p.stdout.readline().strip())
        return score

    def __exit__(self):
        if self.listener:
            self.listener.close()
        if self.meteor_p:
            self.meteor_p.stdin.close()
            self.meteor_p.wait()
