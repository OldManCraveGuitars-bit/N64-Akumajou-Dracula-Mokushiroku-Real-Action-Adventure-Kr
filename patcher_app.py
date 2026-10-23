"""Korean Windows GUI and automation entry point for the v0.6 patcher."""
from __future__ import annotations
import argparse
import ctypes
import json
from pathlib import Path
import queue
import sys
import threading
from patcher_core import VERSION, SOURCE_SHA1, TARGET_SHA256, OUTPUT_NAME, load_bundle, patch_file

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
BUNDLE = ROOT / 'data'

class Patcher:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.root = root
        root.title('악마성 드라큘라 묵시록 한글 패처 v' + VERSION)
        root.geometry('760x650')
        root.minsize(720, 620)
        root.option_add('*Font', ('맑은 고딕', 10))
        self.events = queue.Queue()
        self.busy = False
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value='일본판 원본 롬을 선택하세요.')
        body = ttk.Frame(root, padding=18)
        body.pack(fill='both', expand=True)
        self.title_image = tk.PhotoImage(file=str(BUNDLE / 'title.png')).subsample(2, 2)
        ttk.Label(body, image=self.title_image).pack(pady=(0, 10))
        ttk.Label(body, text='악마성 드라큘라 묵시록 · 한국어 v' + VERSION,
                  font=('맑은 고딕', 14, 'bold')).pack(anchor='w')
        ttk.Label(body, text='일본판 원본 .z64 / .v64 / .n64를 선택하면 별도의 한글 롬을 만듭니다.').pack(anchor='w', pady=(6, 14))
        inputs = ttk.Frame(body)
        inputs.pack(fill='x')
        inputs.columnconfigure(1, weight=1)
        ttk.Label(inputs, text='원본 롬').grid(row=0, column=0, padx=(0, 10), sticky='w')
        self.source_entry = ttk.Entry(inputs, textvariable=self.source)
        self.source_entry.grid(row=0, column=1, sticky='ew', pady=5)
        self.source_button = ttk.Button(inputs, text='찾아보기', command=self.choose_source)
        self.source_button.grid(row=0, column=2, padx=(10, 0))
        ttk.Label(inputs, text='출력 파일').grid(row=1, column=0, padx=(0, 10), sticky='w')
        self.output_entry = ttk.Entry(inputs, textvariable=self.output)
        self.output_entry.grid(row=1, column=1, sticky='ew', pady=5)
        self.output_button = ttk.Button(inputs, text='저장 위치', command=self.choose_output)
        self.output_button.grid(row=1, column=2, padx=(10, 0))
        ttk.Label(body, text='원본은 보존합니다. 영어 메뉴·음성은 유지하고 띄어쓰기는 반각 공백을 씁니다.').pack(anchor='w', pady=(12, 8))
        self.apply_button = ttk.Button(body, text='한글 패치 적용', command=self.start)
        self.apply_button.pack(fill='x', ipady=7)
        self.bar = ttk.Progressbar(body, maximum=100)
        self.bar.pack(fill='x', pady=(12, 6))
        ttk.Label(body, textvariable=self.status).pack(anchor='w')
        from tkinter.scrolledtext import ScrolledText
        self.log = ScrolledText(body, height=9, wrap='word', font=('Consolas', 9))
        self.log.pack(fill='both', expand=True, pady=(8, 0))
        self.write('지원 원본 SHA1 (바이트 순서 정규화 후)\n' + SOURCE_SHA1)
        self.write('한글 결과 SHA256\n' + TARGET_SHA256)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def write(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def choose_source(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title='일본판 원본 롬 선택', filetypes=[('N64 롬', '*.z64 *.v64 *.n64'), ('모든 파일', '*.*')])
        if path:
            self.source.set(path)
            self.output.set(str(Path(path).parent / OUTPUT_NAME))

    def choose_output(self):
        from tkinter import filedialog
        current = Path(self.output.get()) if self.output.get() else Path(OUTPUT_NAME)
        path = filedialog.asksaveasfilename(title='새 한글 롬 저장 위치', initialfile=current.name,
                                           initialdir=str(current.parent), defaultextension='.z64',
                                           filetypes=[('N64 big endian 롬', '*.z64')], confirmoverwrite=False)
        if path:
            self.output.set(path)

    def start(self):
        from tkinter import messagebox
        if self.busy:
            return
        if not self.source.get().strip() or not self.output.get().strip():
            messagebox.showerror('파일 선택', '원본 롬과 출력 파일 경로를 선택하세요.')
            return
        source, output = Path(self.source.get()), Path(self.output.get())
        self.busy = True
        for control in [self.source_entry, self.output_entry, self.source_button, self.output_button, self.apply_button]:
            control.configure(state='disabled')
        self.bar['value'] = 0
        def worker():
            try:
                result = patch_file(source, output, BUNDLE, lambda value, text: self.events.put(('progress', (value, text))))
                self.events.put(('success', result))
            except Exception as error:
                self.events.put(('failure', str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        from tkinter import messagebox
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'progress':
                    value, text = data
                    self.bar['value'] = value
                    self.status.set(text)
                    self.write(text)
                    continue
                self.busy = False
                for control in [self.source_entry, self.output_entry, self.source_button, self.output_button, self.apply_button]:
                    control.configure(state='normal')
                if kind == 'success':
                    self.status.set('완료 · 결과 SHA256 검증 통과')
                    self.write('저장 위치\n' + data['output'] + '\n\nSHA256\n' + data['target_sha256'])
                    messagebox.showinfo('패치 완료', '한글 롬을 만들었습니다.\n새 롬을 부팅한 뒤 게임 안의 저장 데이터를 불러오세요.\n\n' + data['output'])
                else:
                    self.status.set('패치를 적용하지 못했습니다.')
                    self.write('오류: ' + data)
                    messagebox.showerror('패치 실패', data)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            self.status.set('파일 저장이 끝나면 창을 닫을 수 있습니다.')
        else:
            self.root.destroy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--gui-self-check', action='store_true')
    args = parser.parse_args()
    try:
        if args.self_test:
            patch, manifest = load_bundle(BUNDLE)
            result = dict(success=True, version=VERSION, embedded_patch_bytes=len(patch),
                          embedded_patch_sha256=manifest['patch_sha256'], target_sha256=TARGET_SHA256)
        elif args.apply:
            if not args.output:
                raise ValueError('--output 경로가 필요합니다.')
            result = dict(success=True, **patch_file(args.apply, args.output, BUNDLE))
        else:
            if sys.platform == 'win32':
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except OSError:
                    pass
            import tkinter as tk
            root = tk.Tk()
            app = Patcher(root)
            if args.gui_self_check:
                root.update_idletasks()
                root.update()
                assert app.title_image.width() > 0 and app.apply_button.winfo_width() > 0
                result = dict(success=True, version=VERSION, gui_created=True, image_loaded=True,
                              window_width=root.winfo_width(), window_height=root.winfo_height())
                root.destroy()
            else:
                root.mainloop()
                return 0
    except Exception as error:
        result = dict(success=False, version=VERSION, error=str(error))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    elif sys.stdout is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['success'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
