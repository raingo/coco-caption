#!/usr/bin/env python

"""
Python source code - replace this with a description of the code and write the code below this text.
"""

import tempfile
import os
import os.path as osp
import sys
import subprocess

class Terp:

    def __init__(self):
        self.this_dir = osp.dirname(osp.abspath(__file__))
        self.terp_src_dir = osp.join(self.this_dir, 'terp-src')
        self.terpa_path = osp.join(self.terp_src_dir, 'bin', 'terpa')

    def compute_score(self, gts, res):
        assert(gts.keys() == res.keys())
        imgIds = gts.keys()
        scores = []

        hyp = []
        refs = []


        this_sys = 'py'
        def gen_line(imgid, sent):
            seg_id = 1
            test_id = 1
            return '%s ([%s][%d][%s][%d])' % (sent, this_sys, test_id, imgid, seg_id)

        for i in imgIds:
            assert(len(res[i]) == 1)
            hyp.append(gen_line(i, res[i][0]))
            for ref in gts[i]:
                refs.append(gen_line(i, ref))

        hyp_file = tempfile.NamedTemporaryFile(delete=False, dir=self.this_dir)
        hyp_file.write('\n'.join(hyp))
        hyp_file.close()

        refs_file = tempfile.NamedTemporaryFile(delete=False, dir=self.this_dir)
        refs_file.write('\n'.join(refs))
        refs_file.close()

        output_prefix = tempfile.NamedTemporaryFile(delete=False, dir=self.this_dir)
        output_prefix.close()
        subprocess.call([self.terpa_path, '-h', hyp_file.name, '-r', refs_file.name, '-n', output_prefix.name, '-o', 'nist'], stdout = open(os.devnull))

        doc_src = output_prefix.name + this_sys + '.doc.scr'
        seg_src = output_prefix.name + this_sys + '.seg.scr'
        sys_src = output_prefix.name + this_sys + '.sys.scr'

        with open(sys_src) as reader:
            fields = reader.readline().split('\t')
            score = float(fields[-2])

        with open(seg_src) as reader:
            scores_dict = {}
            for line in reader:
                fields = line.strip().split('\t')
                scores_dict[fields[2]] = float(fields[-2])
            scores = []
            for i in imgIds:
                scores.append(scores_dict[i])

        for f in [hyp_file.name, refs_file.name, doc_src, sys_src, seg_src, output_prefix.name]:
            os.remove(f)

        return score, scores

    def method(self):
        return "TERP"

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
