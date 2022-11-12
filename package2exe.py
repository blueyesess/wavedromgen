import os

if __name__ == "__main__":
    if os.path.isfile('dist/WaveDromGen.exe'):
        os.remove('dist/WaveDromGen.exe')
    opt = '-F -w -i ./asset/app.ico ./main.py'
    os.system('pyinstaller %s' % opt)
    os.rename('dist/main.exe', 'dist/WaveDromGen.exe')