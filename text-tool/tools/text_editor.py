"""Local desktop editor for the Japanese CV64 Korean translation project."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import threading
import contextlib
import io
import tkinter as tk
from tkinter import ttk,messagebox
from PIL import Image,ImageTk,ImageDraw,ImageFont
from translation_project import Project
from text_codec import ROOT
from native_font import FONT
from native_preview import render


class Editor:
    def __init__(self,root):
        self.root=root;self.project=Project();self.current=None;self.dirty=False
        root.title('악마성 64 한글화 · 텍스트 도구')
        root.geometry('1260x830');root.minsize(940,660)
        root.option_add('*Font','맑은고딕 10')
        bar=ttk.Frame(root,padding=10);bar.pack(fill='x')
        ttk.Label(bar,text='원문·번역 검색').pack(side='left')
        self.query=tk.StringVar();search=ttk.Entry(bar,textvariable=self.query,width=36);search.pack(side='left',padx=8)
        search.bind('<KeyRelease>',lambda e:self.refresh())
        self.only_pending=tk.BooleanVar();ttk.Checkbutton(bar,text='미번역만',variable=self.only_pending,command=self.refresh).pack(side='left')
        self.group=tk.StringVar(value='전체')
        groups=['전체']+sorted({s['id'].split(':')[0] for s in self.project.segments})
        combo=ttk.Combobox(bar,textvariable=self.group,values=groups,state='readonly',width=17);combo.pack(side='left',padx=8)
        combo.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        ttk.Button(bar,text='저장  Ctrl+S',command=self.save).pack(side='right')
        ttk.Button(bar,text='검증',command=self.validate).pack(side='right',padx=6)
        pane=ttk.Panedwindow(root,orient='horizontal');pane.pack(fill='both',expand=True,padx=10)
        left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=1);pane.add(right,weight=2)
        self.tree=ttk.Treeview(left,columns=('state','source'),show='headings',selectmode='browse')
        self.tree.heading('state',text='상태');self.tree.heading('source',text='원문')
        self.tree.column('state',width=55,stretch=False);self.tree.column('source',width=350)
        scroll=ttk.Scrollbar(left,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.selected)
        self.location=ttk.Label(right,text='문장을 선택하세요.');self.location.pack(anchor='w',padx=12,pady=(4,8))
        ttk.Label(right,text='원문 · 읽기 전용').pack(anchor='w',padx=12)
        self.source=tk.Text(right,height=8,wrap='word',font=('맑은 고딕',12),background='#f3f3f3')
        self.source.pack(fill='x',padx=12,pady=(4,12));self.source.configure(state='disabled')
        ttk.Label(right,text='한국어 번역 · 띄어쓰기는 반각 공백').pack(anchor='w',padx=12)
        self.target=tk.Text(right,height=9,wrap='word',undo=True,font=('맑은 고딕',12))
        self.target.pack(fill='x',padx=12,pady=4)
        self.target.bind('<<Modified>>',self.modified)
        ttk.Label(right,text='실제 롬 글꼴 미리보기 · 공백 8픽셀').pack(anchor='w',padx=12,pady=(12,4))
        self.preview=ttk.Label(right);self.preview.pack(fill='both',expand=True,padx=12,anchor='nw')
        self.width_info=ttk.Label(right,text='');self.width_info.pack(anchor='w',padx=12,pady=6)
        ttk.Label(right,text='영어 문구와 제어 코드를 보존합니다. 캐릭터 이름은 모든 화면에서 한글화합니다.').pack(anchor='w',padx=12,pady=8)
        bottom=ttk.Frame(root,padding=10);bottom.pack(fill='x')
        self.status=ttk.Label(bottom);self.status.pack(side='left')
        ttk.Button(bottom,text='다음 미번역',command=self.next_pending).pack(side='right')
        self.build_button=ttk.Button(bottom,text='시험 롬 빌드',command=self.build)
        self.build_button.pack(side='right',padx=8)
        root.bind('<Control-s>',lambda e:self.save())
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.refresh()

    def refresh(self):
        selected=self.current
        for item in self.tree.get_children():self.tree.delete(item)
        q=self.query.get().casefold()
        for s in self.project.segments:
            t=self.project.target(s)
            if self.only_pending.get() and t:continue
            if self.group.get()!='전체' and not s['id'].startswith(self.group.get()+':'):continue
            if q and q not in (s['source']+'\n'+t+'\n'+s['id']).casefold():continue
            self.tree.insert('', 'end',iid=s['id'],values=('번역됨' if t else '미번역',s['source'].replace('\n',' ')))
        stats=self.project.stats();self.status.configure(text=f"번역 {stats['translated']} / {stats['total']} · 미번역 {stats['pending']} · 한글 {stats['hangul_syllables']}종")
        if selected and self.tree.exists(selected):self.tree.selection_set(selected)

    def selected(self,event=None):
        selection=self.tree.selection()
        if not selection:return
        key=selection[0]
        if key==self.current:return
        if self.dirty and self.current:
            answer=messagebox.askyesnocancel('저장','현재 번역을 저장할까요?')
            if answer is None:
                self.tree.selection_set(self.current);return
            if answer and not self.save():return
        self.current=key;s=self.project.by_id[key]
        self.location.configure(text=key)
        self.source.configure(state='normal');self.source.delete('1.0','end');self.source.insert('1.0',s['source']);self.source.configure(state='disabled')
        self.target.delete('1.0','end');self.target.insert('1.0',self.project.target(s));self.target.edit_modified(False);self.dirty=False
        self.render_preview()

    def modified(self,event=None):
        if self.target.edit_modified():
            self.dirty=True;self.target.edit_modified(False);self.render_preview()

    def render_preview(self):
        text=self.target.get('1.0','end-1c')
        image,widths=render(text)
        image=image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST)
        self.preview_image=ImageTk.PhotoImage(image)
        self.preview.configure(image=self.preview_image)
        self.width_info.configure(text=f"{len(text)}자 · 최대 줄 폭 {max(widths,default=0)}픽셀"+(' · 게임 창 240픽셀 초과' if max(widths,default=0)>240 else ''))

    def save(self):
        if not self.current:return True
        try:self.project.save(self.current,self.target.get('1.0','end-1c'))
        except (ValueError,OSError) as error:messagebox.showerror('저장 실패',str(error));return False
        self.dirty=False;self.refresh();return True

    def validate(self):
        if not self.save():return
        errors=self.project.validate()
        messagebox.showinfo('검증', '\n'.join(f'{k}: {v}' for k,v in errors[:20]) if errors else '전각 공백·미번역 문자·영어 보존 검사 통과')

    def next_pending(self):
        children=list(self.tree.get_children())
        start=children.index(self.current)+1 if self.current in children else 0
        for key in children[start:]+children[:start]:
            if not self.project.target(self.project.by_id[key]):
                self.tree.selection_set(key);self.tree.see(key);return

    def build(self):
        if not self.save():return
        self.build_button.configure(state='disabled');self.status.configure(text='텍스트 시험 롬을 만드는 중...')
        self.build_result=None
        def worker():
            log=io.StringIO()
            try:
                import build
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):build.main()
                self.build_result=(True,log.getvalue())
            except Exception as error:self.build_result=(False,str(error)+'\n'+log.getvalue())
        threading.Thread(target=worker,daemon=True).start()
        self.root.after(150,self.build_poll)

    def build_poll(self):
        if self.build_result is None:self.root.after(150,self.build_poll);return
        success,log=self.build_result;self.build_button.configure(state='normal');self.refresh()
        messagebox.showinfo('시험 빌드' if success else '빌드 실패',
            ('현재 번역과 한글 로고를 반영한 롬을 만들었습니다. 수정한 대사는 게임에서도 확인하세요.\n\n' if success else '')+log[-3500:])

    def close(self):
        if self.dirty:
            answer=messagebox.askyesnocancel('종료','수정한 번역을 저장할까요?')
            if answer is None:return
            if answer and not self.save():return
        self.root.destroy()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--self-check',action='store_true');args=parser.parse_args()
    root=tk.Tk();editor=Editor(root)
    if args.self_check:
        first=next(s for s in editor.project.segments if editor.project.target(s))
        editor.tree.selection_set(first['id']);editor.selected();root.update_idletasks();root.update()
        assert editor.preview_image.width()>0 and editor.tree.get_children()
        print(json.dumps({'ui_created':True,'rows':len(editor.tree.get_children()),'stats':editor.project.stats()},ensure_ascii=False))
        root.destroy()
    else:root.mainloop()
