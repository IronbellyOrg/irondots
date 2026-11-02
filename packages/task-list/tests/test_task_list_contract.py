"""Static instructional-contract checks, not live provider or behavioral execution tests."""
from pathlib import Path
import unittest
import os
ROOT=Path(os.environ.get('TASK_LIST_SKILL_ROOT', str(Path(__file__).resolve().parents[1])))
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.s=(ROOT/'SKILL.md').read_text();c.t=(ROOT/'assets/task-list.md').read_text()
 def test_small_package(self):self.assertLess(len(self.s.split()),1600);self.assertFalse((ROOT/'scripts').exists())
 def test_states(self):
  for x in ('backlog','in_progress','blocked','done','cancelled'):self.assertIn('`'+x+'`',self.s)
 def test_identity_version_guard(self):
  for x in ('same Library file ID','expected-current-version guard','human edits','same ID back to To Do'):self.assertIn(x,self.s)
 def test_uncertainty_not_replay(self):
  for x in ('Reconcile uncertain effects before any retry','never replay verified work','actual destination unknown'):self.assertIn(x,self.s)
 def test_completion_evidence(self):
  for x in ('observable acceptance passes','required delivery','Any required gap prevents','cancellation alone is not'):self.assertIn(x,self.s)
 def test_provider_owned_routes(self):
  for x in ('ClickUp AI performs **all**','No direct domain-read/write fallback','task-list-progress-v0.1.md','dot-reporting/1.0'):self.assertIn(x,self.s)
 def test_authority(self):
  for x in ('Planning does not authorize execution','ClickUp is authoritative','actual observed destination statuses','no competing truth'):self.assertIn(x,self.s)
 def test_template_resume_fields(self):
  for x in ('List ID','Space file ID / expected version','Acceptance check','Source updated_at / fetched_at','Last successful sync','Operation / payload identity','uncertain effects','completed_at'):self.assertIn(x,self.t)
if __name__=='__main__':unittest.main(verbosity=2)
