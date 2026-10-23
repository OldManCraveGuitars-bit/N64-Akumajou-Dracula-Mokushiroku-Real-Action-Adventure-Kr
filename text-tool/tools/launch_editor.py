"""Open the editor, preparing private ROM assets on first use if necessary."""
import tkinter as tk
from tkinter import filedialog,messagebox
from text_codec import ROOT

def main():
    root=tk.Tk();root.withdraw()
    if not (ROOT/'work/manifest.json').exists():
        path=filedialog.askopenfilename(parent=root,title='일본판 원본 롬 선택',filetypes=[('N64 ROM','*.n64 *.z64 *.v64'),('모든 파일','*.*')])
        if not path:root.destroy();return
        try:
            from prepare_project import prepare
            prepare(path)
        except Exception as error:
            messagebox.showerror('원본 준비 실패',str(error),parent=root);root.destroy();return
    from text_editor import Editor
    root.deiconify();Editor(root);root.mainloop()

if __name__=='__main__':main()
