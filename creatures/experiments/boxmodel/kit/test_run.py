"""Runner regressions: isolated evidence and failed-process/failed-gate propagation.

Run with python -m unittest discover -s experiments/boxmodel/kit -p test_run.py.
No Blender execution or canonical creature artifacts are used.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run as runner


class RunnerEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.program = self.source / 'creature.py'
        self.program.write_text('# test creature\n', encoding='utf-8')
        (self.source / 'blueprint.json').write_text('{}', encoding='utf-8')
        (self.source / 'stage1_lock.json').write_text('{"sentinel": "saved lock"}', encoding='utf-8')
        (self.source / 'part_guide.npz').write_bytes(b'saved cache')
        reference = self.source / 'reference'
        reference.mkdir()
        (reference / 'refs.json').write_text('{"sentinel": "saved reference"}', encoding='utf-8')
        (reference / 'sheet.png').write_bytes(b'saved reference bytes')
        canonical = self.source / 'blockout'
        canonical.mkdir()
        (canonical / 'blockout.json').write_text('{"gates_ok": true, "sentinel": "old packet"}', encoding='utf-8')
        self.output = self.root / 'evaluation'

    def fake_build(self, rc=0, lines=None, export=True):
        if lines is None:
            lines = ['BMK PASS scene gate', 'BMK SUMMARY {"ok": true, "stage": 1}', 'BMK OK in 1.0s']

        def build(program, args, log):
            out = Path(args[args.index('--out') + 1])
            stage = args[args.index('--stage') + 1]
            if export:
                sdir = out / ('stage' + stage)
                sdir.mkdir(exist_ok=True)
                (sdir / ('creature.glb' if stage == '4' else 's' + stage + '.glb')).write_bytes(b'glTF')
            if '--blockout' in args:
                packet = out / 'blockout'
                packet.mkdir(exist_ok=True)
                (packet / 'blockout.json').write_text('{"gates_ok": true}', encoding='utf-8')
            Path(log).write_text('\n'.join(lines), encoding='utf-8')
            return rc, lines, []
        return build

    def invoke(self, *flags, rc=0, lines=None, export=True, orbit_rc=0, glbcheck_rc=0):
        argv = [str(self.program), '--out', str(self.output), *flags]
        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(runner, 'blender', side_effect=self.fake_build(rc, lines, export)), \
                mock.patch.object(runner, 'blockout', return_value=0), \
                mock.patch.object(runner, 'sheet', return_value=None), \
                mock.patch.object(runner, 'orbit', return_value=(orbit_rc, ['orbit result'])), \
                mock.patch.object(runner, 'glbcheck', return_value=(glbcheck_rc, ['contract result'])):
            code = runner.main(argv)
        summary = json.loads((self.output / 'gate_summary.json').read_text(encoding='utf-8'))
        return code, summary

    def test_isolated_stage_copies_and_hashes_inputs_without_touching_source(self):
        before = {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        code, summary = self.invoke('--stage', '1', '--no-orbit')
        self.assertEqual(code, 0)
        self.assertTrue(summary['overall_ok'])
        self.assertEqual(before, {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()})
        self.assertEqual((self.output / 'part_guide.npz').read_bytes(), b'saved cache')
        self.assertEqual((self.output / 'reference' / 'sheet.png').read_bytes(), b'saved reference bytes')
        receipt = json.loads((self.output / 'run_receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['program']['sha256'], hashlib.sha256(self.program.read_bytes()).hexdigest())
        self.assertIn('reference/sheet.png', {f['path'] for f in receipt['inputs']})
        self.assertEqual(Path(receipt['scratch']), self.output / '_scratch')
        self.assertFalse((self.output / 'blockout').exists())

    def test_failed_blender_process_cannot_pass_a_blockout(self):
        code, summary = self.invoke('--stage', '1', '--blockout', rc=7)
        self.assertEqual(code, 2)
        self.assertFalse(summary['overall_ok'])
        self.assertEqual(summary['blender']['returncode'], 7)
        self.assertNotIn('packet', summary)

    def test_failed_scene_gate_cannot_be_overruled_by_pass_packet(self):
        code, summary = self.invoke('--blockout', lines=['BMK FAIL scene gate', 'BMK NOT OK in 1.0s'])
        self.assertEqual(code, 1)
        self.assertFalse(summary['overall_ok'])
        self.assertEqual(summary['packet']['returncode'], 0)
        self.assertTrue(summary['blender']['failures'])

    def test_missing_completion_marker_cannot_pass_a_packet(self):
        code, summary = self.invoke('--blockout', lines=['BMK PASS scene gate'])
        self.assertEqual(code, 1)
        self.assertFalse(summary['blender']['terminal_ok'])

    def test_failed_orbit_fails_the_stage(self):
        code, summary = self.invoke('--stage', '1', orbit_rc=5)
        self.assertEqual(code, 1)
        self.assertEqual(summary['orbit']['returncode'], 5)
        self.assertFalse(summary['overall_ok'])

    def test_missing_export_fails_even_when_orbit_is_skipped(self):
        code, summary = self.invoke('--stage', '1', '--no-orbit', export=False)
        self.assertEqual(code, 1)
        self.assertFalse(summary['export']['exists'])

    def test_missing_stage_export_also_fails_a_blockout(self):
        code, summary = self.invoke('--blockout', export=False)
        self.assertEqual(code, 1)
        self.assertFalse(summary['export']['exists'])
        self.assertEqual(summary['packet']['returncode'], 0)

    def test_final_glb_contract_failure_fails_the_stage(self):
        code, summary = self.invoke('--stage', '4', '--no-orbit', glbcheck_rc=1)
        self.assertEqual(code, 1)
        self.assertEqual(summary['glbcheck']['returncode'], 1)
        self.assertFalse(summary['overall_ok'])

    def test_real_composer_rejects_missing_images_and_no_render_packets(self):
        for no_render in ('', '1'):
            self.output = self.root / ('real-packet-' + (no_render or 'rendered'))
            with self.subTest(BMK_NORENDER=no_render), contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.dict(os.environ, {'BMK_NORENDER': no_render}), \
                    mock.patch.object(runner, 'blender', side_effect=self.fake_build()):
                code = runner.main([str(self.program), '--blockout', '--out', str(self.output)])
            summary = json.loads((self.output / 'gate_summary.json').read_text(encoding='utf-8'))
            self.assertEqual(code, 2)
            self.assertTrue(summary['blender']['ok'])
            self.assertTrue(summary['packet']['gates_ok'])
            self.assertFalse(summary['packet']['complete'])
            self.assertEqual(summary['packet']['returncode'], 2)
            self.assertTrue(any(p.endswith('grey_hero_clay.png') for p in summary['packet']['missing']))
            self.assertTrue(any(p.endswith('topology.json') for p in summary['packet']['missing']))
            self.assertFalse(summary['overall_ok'])

    def test_real_composer_rejects_a_missing_reference_mask(self):
        import numpy as np
        base_build = self.fake_build()

        def missing_reference_build(program, args, log):
            result = base_build(program, args, log)
            out = Path(args[args.index('--out') + 1])
            scratch = Path(args[args.index('--scratch') + 1])
            packet, raw = out / 'blockout', scratch / 'blockout'
            raw.mkdir()
            info = dict(gates_ok=True, frame=dict(centre=[0, 0, 0], size=[1, 1, 1], ortho=1.2),
                        poses=dict(fold={}, swing={}, crouch={}), iou=dict(side=1))
            (packet / 'blockout.json').write_text(json.dumps(info), encoding='utf-8')
            (packet / 'topology.json').write_text('{}', encoding='utf-8')
            (packet / 'profiles.json').write_text('{"source": {"guide": false}}', encoding='utf-8')
            (raw / 'topo_shots.json').write_text('{"close": ["joint"]}', encoding='utf-8')
            inputs, _, _ = runner.blockout_inventory(str(out), str(scratch), info)
            for path in inputs:
                if path.endswith('.png'):
                    runner.Image.new('RGB', (16, 16), 'grey').save(path)
            np.savez(raw / 'sil.npz', model_side=np.ones((16, 16), dtype=bool))
            return result

        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.dict(os.environ, {'BMK_NORENDER': ''}), \
                mock.patch.object(runner, 'blender', side_effect=missing_reference_build):
            code = runner.main([str(self.program), '--blockout', '--out', str(self.output)])
        summary = json.loads((self.output / 'gate_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(code, 2)
        self.assertTrue(summary['blender']['ok'])
        self.assertFalse(summary['packet']['complete'])
        self.assertIn('sil.npz lacks masks: ref_side', summary['packet']['issues'])

    @unittest.skipUnless(os.name == 'nt', 'requires Windows drive semantics')
    def test_real_stage_sheet_supports_output_on_another_drive(self):
        if os.path.splitdrive(str(self.output))[0].lower() == os.path.splitdrive(runner.ROOT)[0].lower():
            self.skipTest('temporary output is on the repository drive')
        base_build = self.fake_build()

        def rendered_build(program, args, log):
            result = base_build(program, args, log)
            out = Path(args[args.index('--out') + 1])
            runner.Image.new('RGB', (16, 16), 'grey').save(out / 'stage1' / 's1_hero_clay.png')
            return result

        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(runner, 'blender', side_effect=rendered_build):
            code = runner.main([str(self.program), '--stage', '1', '--no-orbit', '--out', str(self.output)])
        summary = json.loads((self.output / 'gate_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(code, 0)
        self.assertTrue(summary['round_sheet']['complete'])
        self.assertTrue((self.output / 'rounds' / 's1_r00.jpg').is_file())
        self.assertNotIn('error', summary)

    def test_existing_evidence_and_source_trees_are_rejected(self):
        self.output.mkdir()
        sentinel = self.output / 'sentinel.txt'
        sentinel.write_text('keep this evidence', encoding='utf-8')
        for target in (self.output, self.source, self.source / 'nested-output', self.root):
            with self.subTest(target=target), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as raised:
                runner.main([str(self.program), '--blockout', '--out', str(target)])
            self.assertEqual(raised.exception.code, 2)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep this evidence')
        self.assertFalse((self.source / 'nested-output').exists())


if __name__ == '__main__':
    unittest.main()
