"""Conservative native gameplay page layout audit, including choice rows."""
import json,struct
from translation_project import Project,read_json
from text_codec import ROOT
from native_preview import line_width
from build import rebuild_block

def main():
    project=Project();characters=sorted({c for s in project.segments for c in project.target(s) if ord(c)>127})
    glyph_map={c:0x3000+i for i,c in enumerate(characters)};reverse={v:c for c,v in glyph_map.items()}
    issues=[]
    for block in read_json(ROOT/'analysis/selected-blocks.json'):
        if not block['source'].startswith('asset_') or not 60<=int(block['source'].split('_')[1])<=87:continue
        data,_=rebuild_block(block,project,glyph_map);words=struct.unpack('>'+'H'*(len(data)//2),data)
        x=y=maximum=0;message=None;visible=[];skip_newline=False
        def finish():
            if maximum>=4:issues.append(dict(block=block['id'],message=message,lines=maximum+1,text=''.join(visible)))
        for word in list(words)+[0xFFFF]:
            if word==0xFFFF or word&0xFF00==0xA000:
                finish();x=y=maximum=0;visible=[];message=word&255 if word!=0xFFFF else None;skip_newline=False
            elif word&0xFF00==0xA300:
                finish();x=y=maximum=0;visible=[];skip_newline=True
            elif word==1:
                if skip_newline:skip_newline=False
                else:y+=1;x=0;visible.append('\n')
            elif word&0xFF00==0xAA00:
                if x:y+=1;x=0;visible.append('\n')
            elif word>=0xA000:continue
            else:
                skip_newline=False
                char=reverse.get(word,chr(word+0x1E) if 2<=word<0x60 else '?')
                width=line_width(char)
                if x+width>240:y+=1;x=0;visible.append('\n')
                x+=width;maximum=max(maximum,y);visible.append(char)
    (ROOT/'analysis/gameplay-page-layout.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(issues,ensure_ascii=False,indent=2))
    return issues

if __name__=='__main__':main()
