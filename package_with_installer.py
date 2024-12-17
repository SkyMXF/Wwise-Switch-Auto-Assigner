import os
import shutil
import stat

import PyInstaller.__main__

INPUT_PY = "main.py"
BUILD_CACHE_DIR = "__build_cache__"
SPEC_DIR = os.path.join(BUILD_CACHE_DIR, "spec")
WORK_DIR = os.path.join(BUILD_CACHE_DIR, "build")
DIST_DIR = os.path.join(BUILD_CACHE_DIR, "dist")
RELEASE_DIR = "."
EXE_NAME = "SwitchAutoAssigner"


if __name__ == '__main__':

    # prepare build cache dir
    os.makedirs(BUILD_CACHE_DIR, exist_ok=True)

    # run pyinstaller
    params = [
        "-F", INPUT_PY,
        "-n", EXE_NAME,
        "--specpath", SPEC_DIR,
        "--distpath", DIST_DIR,
        "--workpath", WORK_DIR,
    ]

    PyInstaller.__main__.run(params)

    # copy exe to release dir
    exe_src_path = os.path.join(DIST_DIR, f"{EXE_NAME}.exe")
    exe_aim_path = os.path.join(RELEASE_DIR, f"{EXE_NAME}.exe")
    if os.path.exists(exe_aim_path):
        # remove read-only attribute and remove file
        os.chmod(exe_aim_path, stat.S_IWRITE)
        os.remove(exe_aim_path)
    shutil.copy(exe_src_path, exe_aim_path)
