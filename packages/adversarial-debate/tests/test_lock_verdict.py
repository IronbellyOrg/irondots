import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_isolation import isolated
from test_validate_record import SCRIPT

spec=importlib.util.spec_from_file_location('lock_helper',SCRIPT.with_name('lock_verdict.py'))
lock=importlib.util.module_from_spec(spec);spec.loader.exec_module(lock)

class LockTests(unittest.TestCase):
    def test_save_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock'].update(digest=receipt['digest'],artifact=receipt['artifact'])
            self.assertEqual(lock.verify_lock(r,p),[])
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'verdict.json';lock.create_lock(isolated(),p)
            original=p.read_bytes()
            with self.assertRaises(FileExistsError):lock.create_lock(isolated(),p)
            self.assertEqual(p.read_bytes(),original)
    def test_no_package_output(self):
        with self.assertRaises(ValueError):lock.create_lock(isolated(),SCRIPT.parent/'forbidden-fixture.json')
    def test_no_symlink_destination(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'link';p.symlink_to(Path(d)/'original')
            with self.assertRaises(ValueError):lock.create_lock(isolated(),p)
    def test_modified_file_detected(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock']['digest']=receipt['digest'];p.write_bytes(p.read_bytes()+b' ')
            self.assertIn('locked verdict digest does not match exact file bytes',lock.verify_lock(r,p))
    def test_changed_recommendation_detected(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock']['digest']=receipt['digest'];r['recommendation']['selected_ids']=['B']
            self.assertTrue(lock.verify_lock(r,p))
    def test_original_packet_manifest_change_detected(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock']['digest']=receipt['digest'];r['isolation']['packets'][0]['digest']='f'*64
            self.assertTrue(lock.verify_lock(r,p))
    def test_postlock_prior_packet_does_not_change_source_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock']['digest']=receipt['digest'];r['isolation']['packets'].append(dict(id='old',kind='prior_run',source_snapshot_ids=[],digest='d'*64,origin_run_id='r0'))
            self.assertEqual(lock.verify_lock(r,p),[])
    def test_postlock_reporting_does_not_change_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();p=Path(d)/'verdict.json';receipt=lock.create_lock(r,p);r['isolation']['verdict_lock']['digest']=receipt['digest'];r['reporting']={'receipt':'post-lock'};r['isolation']['prior_results']['state']='revealed'
            self.assertEqual(lock.verify_lock(r,p),[])
    def test_cli_lock_then_validate(self):
        with tempfile.TemporaryDirectory() as d:
            r=isolated();source=Path(d)/'result.json';dest=Path(d)/'lock.json';source.write_text(json.dumps(r))
            proc=subprocess.run([sys.executable,'-B',str(SCRIPT.with_name('lock_verdict.py')),str(source),str(dest)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout);receipt=json.loads(proc.stdout);r['isolation']['verdict_lock'].update(digest=receipt['digest'],artifact=receipt['artifact']);source.write_text(json.dumps(r))
            proc=subprocess.run([sys.executable,'-B',str(SCRIPT),str(source),'--locked-verdict',str(dest)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout)
    def test_missing_and_wrong_input(self):
        with self.assertRaises(ValueError):lock.snapshot({'contract_version':'dot-adversarial-result/1.0'})
        r=isolated();r.pop('criteria')
        with self.assertRaises(ValueError):lock.snapshot(r)

if __name__=='__main__':unittest.main()
