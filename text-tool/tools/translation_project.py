"""Shared project model for the editor and reproducible ROM builder."""
from __future__ import annotations
from pathlib import Path
import json
import re
from collections import Counter
from text_codec import ROOT

# User-requested character names are localized in the shared menu table.
# Every other Latin word remains subject to the preservation check.
ENGLISH_LOCALIZATION_EXCEPTIONS={
    'rom:0F21A8':'Reinhardt', 'rom:0F21BC':'Carrie',
    'rom:0F21CA':'Cornel', 'rom:0F21D8':'Coller',
}


def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))


class Project:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        self.segments=read_json(self.root/'translation/segments.json')
        self.by_id={s['id']:s for s in self.segments}
        self.explicit={}
        for path in sorted((self.root/'translation').glob('ko*.json')):
            self.explicit.update(read_json(path))
        self.user_path=self.root/'translation/user_edits.json'
        self.user=read_json(self.user_path) if self.user_path.exists() else {}
        self.explicit.update(self.user)
        self.memory={}
        for key,target in self.explicit.items():
            if key in self.by_id:self.memory[self.by_id[key]['source']]=target

    def target(self,segment):
        return self.explicit.get(segment['id'],self.memory.get(segment['source'],''))

    def save(self,key,target):
        if '\u3000' in target:raise ValueError('띄어쓰기에는 반각 공백을 사용하세요.')
        if any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in target):
            raise ValueError('번역문에 일본어 또는 한자가 남아 있습니다.')
        if key not in self.by_id:raise KeyError(key)
        self.user[key]=target
        self.explicit[key]=target
        self.memory[self.by_id[key]['source']]=target
        temp=self.user_path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.user,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temp.replace(self.user_path)

    def validate(self):
        from native_preview import line_width
        errors=[]
        for s in self.segments:
            t=self.target(s)
            if not t:continue
            if '\u3000' in t:errors.append((s['id'],'전각 공백'))
            if any('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in t):errors.append((s['id'],'미번역 문자'))
            limit=240
            if s['id'].startswith('rom:') and 0xF1EE4<=int(s['id'].split(':')[1],16)<=0xF20D0:limit=150
            if s['id'] in ('asset_174:0029E8','asset_174:0029FA'):limit=100
            if s['id']=='asset_174:002A22':limit=96
            if s['id'] in ENGLISH_LOCALIZATION_EXCEPTIONS:limit=96
            if any(line_width(line)>limit for line in t.split('\n')):errors.append((s['id'],f'게임 창의 {limit}픽셀 폭 초과'))
            # Latin runs inside Japanese prose are part of the user's English-preservation requirement.
            source_runs=Counter(re.findall(r'[A-Za-z0-9]*[A-Za-z][A-Za-z0-9]*',re.sub(r'<[0-9A-F]{4}>','',s['source'])))
            target_runs=Counter(re.findall(r'[A-Za-z0-9]*[A-Za-z][A-Za-z0-9]*',t))
            if ENGLISH_LOCALIZATION_EXCEPTIONS.get(s['id'])==s['source']:continue
            for run,count in source_runs.items():
                if target_runs[run]<count:errors.append((s['id'],f'영어 보존 확인: {run}'))
        return errors

    def stats(self):
        translated=sum(bool(self.target(s)) for s in self.segments)
        glyphs={c for s in self.segments for c in self.target(s) if '\uac00'<=c<='\ud7a3'}
        return dict(total=len(self.segments),translated=translated,pending=len(self.segments)-translated,
                    hangul_syllables=len(glyphs))


if __name__=='__main__':
    p=Project();print(json.dumps(p.stats(),ensure_ascii=False,indent=2))
    for error in p.validate():print(*error)
