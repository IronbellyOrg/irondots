"""Run tests and retain unique timestamped JSON/text receipts without overwriting."""
import io, json, pathlib, unittest, datetime, hashlib
root = pathlib.Path(__file__).resolve().parent
suite = unittest.defaultTestLoader.discover(str(root), pattern='test_*.py')
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
now = datetime.datetime.now(datetime.timezone.utc)
stamp = now.strftime('%Y%m%dT%H%M%S%fZ')
out = root/'runs'; out.mkdir(exist_ok=True)
(out/(stamp+'.txt')).write_text(stream.getvalue())
payload = {'generated_at':now.isoformat(), 'evidence_level':'offline synthetic policy model only', 'tests_run':result.testsRun,
           'failures':[(str(t),trace) for t,trace in result.failures], 'errors':[(str(t),trace) for t,trace in result.errors],
           'skipped':result.skipped, 'successful':result.wasSuccessful(),
           'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')}}
(out/(stamp+'.json')).write_text(json.dumps(payload,indent=2))
print(stream.getvalue()); print(json.dumps(payload,indent=2))
raise SystemExit(0 if result.wasSuccessful() else 1)
