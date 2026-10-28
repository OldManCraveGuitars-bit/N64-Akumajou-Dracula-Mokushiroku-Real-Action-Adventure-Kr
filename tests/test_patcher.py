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

    def test_actual_rom_menu_prompts_and_shared_character_names(self):
        import struct
        from bps import apply
        sys.path.insert(0,str(ROOT/'text-tool/tools'))
        try:
            from translation_project import Project,read_json
            from native_font import encode
            from lzkn64 import decompress
            from build import rebuild_block
            project=Project(ROOT/'text-tool')
            glyphs={c:0x3000+i for i,c in enumerate(sorted({c for s in project.segments for c in project.target(s) if ord(c)>127}))}
            patch,_=load_bundle(ROOT/'data');target=apply(self.normalized,patch)
            blocks=read_json(ROOT/'text-tool/analysis/selected-blocks.json')
            menu=next(b for b in blocks if b['id']=='rom:0F2100')
            expected,_=rebuild_block(menu,project,glyphs)
            self.assertEqual(target.count(expected),1)
            self.assertIn(encode('라인하르트',glyphs),expected)
            self.assertIn(encode('캐리',glyphs),expected)
            self.assertNotIn(encode('Reinhardt',glyphs),expected)
            self.assertNotIn(encode('Carrie',glyphs),expected)
            self.assertIn(encode('KEY CONFIG',glyphs),expected)
            for asset_id,text in [(174,'종료할까요?'),(177,'진행할까요?')]:
                start,end=struct.unpack_from('>II',target,0x979CC+asset_id*8)
                data=decompress(target[start&0x7FFFFFFF:end])
                self.assertIn(encode(text,glyphs),data)
                if asset_id==174:
                    self.assertEqual(struct.unpack_from('>f',data,0x2CA4)[0],1.0)
        finally:
            sys.path.pop(0)

    def test_actual_rom_stage_banners_fit_one_line(self):
        import importlib.util,struct
        from bps import apply
        spec=importlib.util.spec_from_file_location('cv64_test_lzkn64',ROOT/'text-tool/tools/lzkn64.py')
        lz=importlib.util.module_from_spec(spec)
        sys.path.insert(0,str(ROOT/'text-tool/tools'))
        try:spec.loader.exec_module(lz)
        finally:sys.path.pop(0)
        patch,_=load_bundle(ROOT/'data');target=apply(self.normalized,patch)
        table_entry=0x979CC+182*8
        def extract(rom):
            start,end=struct.unpack_from('>II',rom,table_entry)
            return lz.decompress(rom[start&0x7FFFFFFF:end])
        original=extract(self.normalized);translated=extract(target)
        segments=json.loads((ROOT/'text-tool/translation/segments.json').read_text(encoding='utf-8'))
        overrides={}
        for path in sorted((ROOT/'text-tool/translation').glob('ko*.json')):
            overrides.update(json.loads(path.read_text(encoding='utf-8')))
        names=[s for s in segments if s['id'].startswith('asset_182:')]
        self.assertEqual(len(names),13)
        widths=struct.unpack_from('>13H',translated,0x854)
        for name,width in zip(sorted(names,key=lambda s:s['id']),widths):
            text=overrides[name['id']]
            self.assertNotIn('\n',text)
            required=sum(8 if c==' ' else 16 for c in text)
            self.assertGreaterEqual(width,required,(text,width,required))
        self.assertEqual(struct.unpack_from('>I',translated,0x2E4)[0],0x240D005A)
        self.assertEqual(original[0x2E4:0x2E8],translated[0x2E4:0x2E8])

if __name__=='__main__':unittest.main()
