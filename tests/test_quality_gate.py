import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from quality_gate import assess


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.quality-gate').mkdir()
        self.policy = {'original_request': 'Keep the original request unchanged', 'requirements': [
            {'id': 'R1', 'text': 'Actually run a command', 'proof': {
                'type': 'command', 'argv': ['python', '-c', 'print("OK")']}}]}
        self.claims = {'overall_claim': 'completed', 'items': [{'id': 'R1', 'status': 'done'}], 'conclusion_changes': []}
        self.save()

    def save(self):
        policy_file = self.root / '.quality-gate/policy.json'
        policy_file.write_text(json.dumps(self.policy), encoding='utf-8')
        (self.root / '.quality-gate/policy.sha256').write_text(hashlib.sha256(policy_file.read_bytes()).hexdigest())
        (self.root / '.quality-gate/claims.json').write_text(json.dumps(self.claims))

    def test_real_command_passes(self):
        self.assertEqual(assess(self.root)['overall'], 'PASS')

    def test_failure_blocks_completion(self):
        self.policy['requirements'][0]['proof']['argv'] = ['python', '-c', 'import sys; sys.exit(13)']
        self.save()
        self.assertEqual(assess(self.root)['overall'], 'FAIL')

    def test_changed_baseline_blocks_completion(self):
        self.policy['original_request'] = 'silent change'
        (self.root / '.quality-gate/policy.json').write_text(json.dumps(self.policy))
        self.assertEqual(assess(self.root)['overall'], 'FAIL')

    def test_missing_original_requirement_fails(self):
        self.claims['items'] = []
        self.save()
        self.assertEqual(assess(self.root)['overall'], 'FAIL')

    def test_unsupported_conclusion_change_fails(self):
        self.claims['conclusion_changes'] = [{'before': 'incomplete', 'after': 'complete', 'new_evidence': []}]
        self.save()
        self.assertEqual(assess(self.root)['overall'], 'FAIL')

    def test_manual_evidence_is_pending(self):
        self.policy['requirements'][0]['proof'] = {'type': 'manual'}
        self.claims['overall_claim'] = 'partial'
        self.save()
        self.assertEqual(assess(self.root)['overall'], 'PENDING')


if __name__ == '__main__':
    unittest.main()
