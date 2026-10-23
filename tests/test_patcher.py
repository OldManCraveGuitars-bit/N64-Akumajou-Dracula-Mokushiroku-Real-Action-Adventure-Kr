import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patcher_core import normalize, patch_file, load_bundle, SOURCE_SHA1, TARGET_SHA256

ROOT=Path(__file__).resolve().parents[1]

class PatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=os.environ.get('CV64_TEST_ROM')
        if not source:raise unittest.SkipTest('Set CV64_TEST_ROM to a separately supplied Japanese original ROM.')
        cls.original=Path(source).resolve()
        cls.source_bytes=cls.original.read_bytes()
        cls.normalized=normalize(cls.source_bytes)
        assert hashlib.sha1(cls.normalized).hexdigest()==SOURCE_SHA1

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cv64-patcher-test-')
        self.folder=Path(self.temp.name)

    def tearDown(self):self.temp.cleanup()

    def test_three_byte_orders(self):
        for width in [1,2,4]:
            with self.subTest(width=width):
                raw=bytearray(len(self.normalized))
                for i in range(width):raw[i::width]=self.normalized[width-1-i::width]
                source=self.folder/f'원본 {width}.rom';source.write_bytes(raw)
                output=self.folder/f'한글 {width}.z64'
                result=patch_file(source,output,ROOT/'data')
                self.assertEqual(result['target_sha256'],TARGET_SHA256)
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),TARGET_SHA256)
                self.assertEqual(source.read_bytes(),raw)

    def test_wrong_original_rejected(self):
        corrupt=bytearray(self.normalized);corrupt[-1]^=1
        source=self.folder/'wrong.z64';source.write_bytes(corrupt)
        with self.assertRaisesRegex(ValueError,'해시가 다릅니다'):
            patch_file(source,self.folder/'out.z64',ROOT/'data')
        self.assertFalse((self.folder/'out.z64').exists())

    def test_original_and_existing_output_protected(self):
        with self.assertRaisesRegex(ValueError,'원본 롬'):
            patch_file(self.original,self.original,ROOT/'data')
        output=self.folder/'existing.z64';output.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):patch_file(self.original,output,ROOT/'data')
        self.assertEqual(output.read_bytes(),b'preserve')
        self.assertEqual(self.original.read_bytes(),self.source_bytes)

    def test_corrupt_patch_rejected(self):
        bundle=self.folder/'data';shutil.copytree(ROOT/'data',bundle)
        manifest=json.loads((bundle/'manifest.json').read_text())
        path=bundle/manifest['patch_file'];data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
        with self.assertRaisesRegex(ValueError,'내장 패치'):
            patch_file(self.original,self.folder/'out.z64',bundle)
        self.assertFalse((self.folder/'out.z64').exists())

    def test_gui_entry_point(self):
        report=self.folder/'gui.json'
        result=subprocess.run([sys.executable,str(ROOT/'patcher_app.py'),'--gui-self-check','--report',str(report)],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        self.assertTrue(json.loads(report.read_text())['image_loaded'])

if __name__=='__main__':unittest.main()
